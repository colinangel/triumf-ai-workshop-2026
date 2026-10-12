"""Seeded Monte Carlo of SiPM and PMT waveforms with full ground truth.

Physics included, per channel:
  * Poisson primary photoelectrons from a light pulse (prompt or exponential emission)
  * single-PE charge fluctuations (gamma distributed, so charges stay positive)
  * optical crosstalk as a branching process (SiPM)
  * afterpulsing, exponential delay with cell recovery (SiPM) or late Gaussian (PMT)
  * dark counts uniform in the record, with their own crosstalk
  * transit-time jitter, white electronic noise, pedestal drift and wander
  * 14-bit quantisation and saturation at the ADC floor (negative-going pulses)

Every photoelectron is recorded in `Run.pe`, so any analysis window can be
checked against truth, not only the standard gate.
"""

from __future__ import annotations

import dataclasses
import json
from dataclasses import dataclass

import numpy as np
import pandas as pd

from wfkit import __version__
from wfkit.config import RunConfig
from wfkit.pulses import sample_pulses

_CHUNK = 8192


@dataclass
class Run:
    config: RunConfig
    waveforms: np.ndarray  # (n_channels, n_events, n_samples) int16 ADC counts
    truth: pd.DataFrame  # one row per (event, channel)
    pe: pd.DataFrame  # one row per photoelectron
    metadata: dict


def _gain_samples(rng: np.random.Generator, n: int, q1: float, spread: float) -> np.ndarray:
    if spread <= 0:
        return np.full(n, q1)
    shape = 1.0 / spread**2
    return rng.gamma(shape, q1 / shape, size=n)


def _branch_crosstalk(rng, event, t, p, origin):
    """Each avalanche fires one neighbour with probability p, recursively."""
    out_e, out_t, out_o = [], [], []
    cur_e, cur_t, cur_o = event, t, origin
    for _ in range(64):
        if cur_e.size == 0 or p <= 0:
            break
        fire = rng.random(cur_e.size) < p
        cur_e, cur_t, cur_o = cur_e[fire], cur_t[fire], cur_o[fire]
        out_e.append(cur_e)
        out_t.append(cur_t)
        out_o.append(cur_o)
    if not out_e:
        return np.empty(0, np.int64), np.empty(0), np.empty(0, dtype=object)
    return np.concatenate(out_e), np.concatenate(out_t), np.concatenate(out_o)


def _channel_pe(cfg: RunConfig, rng: np.random.Generator, n_events: int, t_event: np.ndarray, delay_ns: float) -> pd.DataFrame:
    s, light, d = cfg.sensor, cfg.light, cfg.digitizer
    window_ns = d.n_samples * d.dt_ns

    n_primary = rng.poisson(light.mu, size=n_events) if light.mu > 0 else np.zeros(n_events, np.int64)
    pe_ev = np.repeat(np.arange(n_events), n_primary)
    t = t_event[pe_ev] + delay_ns
    if light.decay_ns > 0:
        t = t + rng.exponential(light.decay_ns, size=pe_ev.size)
    if s.transit_jitter_ns > 0:
        t = t + rng.normal(0.0, s.transit_jitter_ns, size=pe_ev.size)
    prompt_origin = np.full(pe_ev.size, "prompt", dtype=object)

    n_dark = rng.poisson(s.dark_rate_hz * window_ns * 1e-9, size=n_events)
    dk_ev = np.repeat(np.arange(n_events), n_dark)
    dk_t = rng.uniform(0.0, window_ns, size=dk_ev.size)
    dark_origin = np.full(dk_ev.size, "dark", dtype=object)

    seed_e = np.concatenate([pe_ev, dk_ev])
    seed_t = np.concatenate([t, dk_t])
    seed_o = np.concatenate([prompt_origin, dark_origin])
    seed_k = np.concatenate([np.full(pe_ev.size, "prompt", dtype=object), np.full(dk_ev.size, "dark", dtype=object)])

    ct_e, ct_t, ct_o = _branch_crosstalk(rng, seed_e, seed_t, s.crosstalk_prob, seed_o)
    ct_k = np.full(ct_e.size, "crosstalk", dtype=object)

    av_e = np.concatenate([seed_e, ct_e])
    av_t = np.concatenate([seed_t, ct_t])
    av_o = np.concatenate([seed_o, ct_o])
    av_k = np.concatenate([seed_k, ct_k])
    av_q = _gain_samples(rng, av_e.size, cfg.q1_pc, s.gain_spread)

    ap = rng.random(av_e.size) < s.afterpulse_prob
    ap_e, ap_t0, ap_o = av_e[ap], av_t[ap], av_o[ap]
    if s.afterpulse_model == "exponential":
        delay = rng.exponential(s.afterpulse_delay_ns, size=ap_e.size)
    else:
        delay = rng.normal(s.afterpulse_delay_ns, s.afterpulse_delay_sigma_ns, size=ap_e.size)
    ap_q = _gain_samples(rng, ap_e.size, cfg.q1_pc, s.gain_spread)
    if s.recovery_tau_ns > 0:
        ap_q = ap_q * (1.0 - np.exp(-np.clip(delay, 0, None) / s.recovery_tau_ns))

    return (
        pd.DataFrame(
            {
                "event": np.concatenate([av_e, ap_e]).astype(np.int64),
                "t_ns": np.concatenate([av_t, ap_t0 + delay]),
                "charge_pc": np.concatenate([av_q, ap_q]),
                "kind": pd.Categorical(
                    np.concatenate([av_k, np.full(ap_e.size, "afterpulse", dtype=object)]),
                    categories=["prompt", "crosstalk", "afterpulse", "dark"],
                ),
                "origin": pd.Categorical(np.concatenate([av_o, ap_o]), categories=["prompt", "dark"]),
            }
        ),
        n_primary,
        n_dark,
    )


def generate(cfg: RunConfig, n_events: int | None = None, seed: int | None = None) -> Run:
    n_events = cfg.default_events if n_events is None else n_events
    seed = cfg.default_seed if seed is None else seed
    d, s = cfg.digitizer, cfg.sensor
    root = np.random.SeedSequence(seed)
    event_rng, *channel_rngs = (np.random.default_rng(ss) for ss in root.spawn(1 + 2 * cfg.n_channels))
    pulse_rngs, noise_rngs = channel_rngs[: cfg.n_channels], channel_rngs[cfg.n_channels :]

    t_event = np.full(n_events, cfg.trigger_time_ns + cfg.light.offset_ns)
    phase = np.arange(n_events) / max(n_events, 1)
    pedestal = d.pedestal_adc + d.pedestal_drift_adc * np.sin(2 * np.pi * phase) + event_rng.normal(0.0, d.pedestal_jitter_adc, n_events)

    window_ns = d.n_samples * d.dt_ns
    gate_lo, gate_hi = cfg.standard_gate_ns
    waveforms = np.empty((cfg.n_channels, n_events, d.n_samples), dtype=np.int16)
    truth_frames, pe_frames = [], []

    for ch, delay in enumerate(cfg.channel_delays_ns):
        pe, n_primary, n_dark = _channel_pe(cfg, pulse_rngs[ch], n_events, t_event, delay)
        pe.insert(1, "channel", ch)

        signal = np.zeros((n_events, d.n_samples))
        ev = pe["event"].to_numpy()
        t = pe["t_ns"].to_numpy()
        amp_adc_samples = pe["charge_pc"].to_numpy() / cfg.adc_samples_to_pc
        for i in range(0, ev.size, _CHUNK):
            sl = slice(i, i + _CHUNK)
            shapes = sample_pulses(s.pulse, t[sl], d.dt_ns, d.n_samples) * d.dt_ns
            np.add.at(signal, ev[sl], shapes * amp_adc_samples[sl, None])

        raw = (
            pedestal[:, None] - signal + noise_rngs[ch].normal(0.0, d.noise_adc, signal.shape)
            if d.noise_adc > 0
            else pedestal[:, None] - signal
        )
        raw = np.rint(raw)
        saturated = (raw < 0).any(axis=1) | (raw > d.adc_max).any(axis=1)
        waveforms[ch] = np.clip(raw, 0, d.adc_max).astype(np.int16)

        q = pe["charge_pc"].to_numpy()
        kind = pe["kind"].to_numpy()
        origin = pe["origin"].to_numpy()
        f_record = s.pulse.cdf(window_ns - t) - s.pulse.cdf(-t)
        f_gate = s.pulse.cdf(gate_hi - t) - s.pulse.cdf(gate_lo - t)
        prompt_like = origin == "prompt"
        in_gate = (t >= gate_lo) & (t < gate_hi)

        def per_event(mask, weights=None, ev=ev):
            w = None if weights is None else weights[mask]
            return np.bincount(ev[mask], weights=w, minlength=n_events)

        all_mask = np.ones(ev.size, bool)
        truth_frames.append(
            pd.DataFrame(
                {
                    "event": np.arange(n_events),
                    "channel": ch,
                    "n_primary": n_primary,
                    "n_crosstalk": per_event((kind == "crosstalk") & prompt_like).astype(np.int64),
                    "n_prompt": (n_primary + per_event((kind == "crosstalk") & prompt_like)).astype(np.int64),
                    "n_afterpulse": per_event(kind == "afterpulse").astype(np.int64),
                    "n_dark": n_dark,
                    "n_dark_crosstalk": per_event((kind == "crosstalk") & ~prompt_like).astype(np.int64),
                    "n_pe_in_gate": per_event(in_gate).astype(np.int64),
                    "t_light_ns": t_event + delay,
                    "q_prompt_pc": per_event(prompt_like & (kind != "afterpulse"), q),
                    "q_gate_true_pc": per_event(all_mask, q * f_gate),
                    "q_record_true_pc": per_event(all_mask, q * f_record),
                    "pedestal_adc": pedestal,
                    "saturated": saturated,
                }
            )
        )
        pe_frames.append(pe)

    truth = pd.concat(truth_frames, ignore_index=True)
    pe_all = pd.concat(pe_frames, ignore_index=True)
    return Run(config=cfg, waveforms=waveforms, truth=truth, pe=pe_all, metadata=build_metadata(cfg, n_events, seed))


def build_metadata(cfg: RunConfig, n_events: int, seed: int) -> dict:
    d, s = cfg.digitizer, cfg.sensor
    md = {
        "preset": cfg.name,
        "description": cfg.description,
        "n_events": n_events,
        "n_channels": cfg.n_channels,
        "seed": seed,
        "generator_version": __version__,
        "numpy_version": np.__version__,
        "digitizer_model": d.model,
        "dt_ns": d.dt_ns,
        "n_samples": d.n_samples,
        "trigger_sample": d.trigger_sample,
        "adc_bits": d.adc_bits,
        "mv_per_adc": d.mv_per_adc,
        "impedance_ohm": d.impedance_ohm,
        "preamp_gain": s.preamp_gain,
        "polarity": "negative",
        "sensor_kind": s.kind,
        "channel_delays_ns": list(cfg.channel_delays_ns),
        "q1_pc": cfg.q1_pc,
        "standard_gate_ns": list(cfg.standard_gate_ns),
        "standard_baseline_samples": list(cfg.standard_baseline_samples),
        "units": {
            "waveform": "ADC counts, int16, negative-going pulses on a positive pedestal",
            "charge": "pC at the sensor (divide out preamp_gain)",
            "time": "ns from the start of the record",
        },
        "model": {
            "sensor": {k: v for k, v in dataclasses.asdict(s).items() if k != "pulse"},
            "pulse": {"type": type(s.pulse).__name__, **dataclasses.asdict(s.pulse)},
            "light": dataclasses.asdict(cfg.light),
            "digitizer_noise_adc": d.noise_adc,
            "pedestal_adc": d.pedestal_adc,
        },
    }
    return json.loads(json.dumps(md))

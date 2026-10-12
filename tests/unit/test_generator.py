"""Behavioural tests for the synthetic waveform generator.

Each test checks a physical statement about the simulated detector against
the truth the generator records. If one of these fails, the ground truth used
by every lab is untrustworthy, so these run before anything else.
"""

import dataclasses

import numpy as np
import pytest

from wfkit.config import PRESETS
from wfkit.generator import generate


def quiet(cfg, **sensor_overrides):
    """Same run with selected sensor effects switched off."""
    sensor = dataclasses.replace(cfg.sensor, **sensor_overrides)
    return dataclasses.replace(cfg, sensor=sensor)


@pytest.fixture(scope="module")
def lowlight():
    return generate(PRESETS["sipm_lowlight"], n_events=20_000, seed=11)


def test_same_seed_is_bit_identical():
    a = generate(PRESETS["sipm_lowlight"], n_events=500, seed=3)
    b = generate(PRESETS["sipm_lowlight"], n_events=500, seed=3)
    assert np.array_equal(a.waveforms, b.waveforms)
    assert a.truth.equals(b.truth)


def test_different_seed_differs():
    a = generate(PRESETS["sipm_lowlight"], n_events=500, seed=3)
    b = generate(PRESETS["sipm_lowlight"], n_events=500, seed=4)
    assert not np.array_equal(a.waveforms, b.waveforms)


def test_waveform_shape_and_dtype(lowlight):
    d = PRESETS["sipm_lowlight"].digitizer
    assert lowlight.waveforms.shape == (1, 20_000, d.n_samples)
    assert lowlight.waveforms.dtype == np.int16


def test_primary_photoelectrons_are_poisson(lowlight):
    mu = PRESETS["sipm_lowlight"].light.mu
    n = lowlight.truth["n_primary"].to_numpy()
    se = np.sqrt(mu / n.size)
    assert abs(n.mean() - mu) < 4 * se
    assert n.var() == pytest.approx(mu, rel=0.05)


def test_crosstalk_rate_matches_branching_model(lowlight):
    p = PRESETS["sipm_lowlight"].sensor.crosstalk_prob
    t = lowlight.truth
    ratio = t["n_crosstalk"].sum() / t["n_primary"].sum()
    assert ratio == pytest.approx(p / (1 - p), rel=0.06)


def test_dark_count_rate_matches_config(lowlight):
    cfg = PRESETS["sipm_lowlight"]
    window_s = cfg.digitizer.n_samples * cfg.digitizer.dt_ns * 1e-9
    expected = cfg.sensor.dark_rate_hz * window_s
    observed = lowlight.truth["n_dark"].mean()
    assert observed == pytest.approx(expected, rel=0.05)


def _clean_sipm(noise_adc):
    cfg = quiet(PRESETS["sipm_lowlight"], crosstalk_prob=0.0, afterpulse_prob=0.0, dark_rate_hz=0.0, gain_spread=0.0)
    return dataclasses.replace(
        cfg, digitizer=dataclasses.replace(cfg.digitizer, noise_adc=noise_adc, pedestal_drift_adc=0.0, pedestal_jitter_adc=0.0)
    )


def _record_charge(run, cfg):
    wf = run.waveforms[0].astype(np.float64)
    signal = run.truth["pedestal_adc"].to_numpy()[:, None] - wf  # pulses are negative-going
    return signal.sum(axis=1) * cfg.adc_samples_to_pc


def test_charge_closure_with_realistic_noise():
    """Summing the whole record recovers the true charge, unbiased.

    Electronic noise dithers the ADC, so rounding to integer counts averages out.
    """
    cfg = _clean_sipm(noise_adc=3.0)
    run = generate(cfg, n_events=4_000, seed=5)
    resid = _record_charge(run, cfg) - run.truth["q_record_true_pc"].to_numpy()
    sigma_event = cfg.digitizer.noise_adc * np.sqrt(cfg.digitizer.n_samples) * cfg.adc_samples_to_pc
    assert resid.std() == pytest.approx(sigma_event, rel=0.05)
    assert abs(resid.mean()) < 4 * sigma_event / np.sqrt(resid.size)
    one = run.truth["n_primary"].to_numpy() == 1
    assert resid[one].mean() + cfg.q1_pc == pytest.approx(cfg.q1_pc, abs=4 * sigma_event / np.sqrt(one.sum()))


def test_noise_free_quantisation_loses_sub_lsb_tail():
    """Without noise, samples below half an ADC count round to zero and charge is lost.

    This is real digitiser behaviour, kept as a test so nobody "fixes" it by accident,
    and used in the validity module as an example of a bias with no random component.
    """
    cfg = _clean_sipm(noise_adc=0.0)
    run = generate(cfg, n_events=1_000, seed=5)
    resid = _record_charge(run, cfg) - run.truth["q_record_true_pc"].to_numpy()
    one = run.truth["n_primary"].to_numpy() == 1
    assert resid[one].mean() < -0.003 * cfg.q1_pc


def test_gate_truth_is_consistent_with_pe_table(lowlight):
    cfg = PRESETS["sipm_lowlight"]
    pe = lowlight.pe
    pulse = cfg.sensor.pulse
    lo, hi = cfg.standard_gate_ns
    frac = pulse.cdf(hi - pe["t_ns"].to_numpy()) - pulse.cdf(lo - pe["t_ns"].to_numpy())
    contrib = pe["charge_pc"].to_numpy() * frac
    per_event = np.bincount(pe["event"].to_numpy(), weights=contrib, minlength=len(lowlight.truth))
    assert np.allclose(per_event, lowlight.truth["q_gate_true_pc"].to_numpy(), rtol=1e-9, atol=1e-12)


def test_pretrigger_baseline_tracks_true_pedestal(lowlight):
    cfg = PRESETS["sipm_lowlight"]
    lo, hi = cfg.standard_baseline_samples
    clean = lowlight.truth["n_dark"].to_numpy() == 0
    est = np.median(lowlight.waveforms[0][clean, lo:hi], axis=1)
    true = lowlight.truth["pedestal_adc"].to_numpy()[clean]
    assert np.mean(est - true) == pytest.approx(0.0, abs=0.3)


def test_saturation_is_flagged():
    cfg = PRESETS["sipm_lowlight"]
    cfg = dataclasses.replace(cfg, light=dataclasses.replace(cfg.light, mu=400.0))
    run = generate(cfg, n_events=50, seed=2)
    assert run.truth["saturated"].all()
    assert run.waveforms.min() == 0


def test_pmt_has_no_crosstalk_and_wider_gain_spread():
    run = generate(PRESETS["pmt_spe"], n_events=5_000, seed=9)
    assert run.truth["n_crosstalk"].sum() == 0
    pe = run.pe[run.pe["kind"] == "prompt"]
    rel_spread = pe["charge_pc"].std() / pe["charge_pc"].mean()
    assert rel_spread == pytest.approx(PRESETS["pmt_spe"].sensor.gain_spread, rel=0.1)


def test_two_channel_preset_has_known_delay():
    cfg = PRESETS["coincidence"]
    run = generate(cfg, n_events=2_000, seed=1)
    assert run.waveforms.shape[0] == 2
    pe = run.pe[run.pe["kind"] == "prompt"]
    first = pe.groupby(["event", "channel"])["t_ns"].min().unstack()
    both = first.dropna()
    delay = (both[1] - both[0]).median()
    assert delay == pytest.approx(cfg.channel_delays_ns[1] - cfg.channel_delays_ns[0], abs=0.3)


def test_metadata_carries_units_and_provenance(lowlight):
    md = lowlight.metadata
    for key in [
        "dt_ns",
        "n_samples",
        "trigger_sample",
        "mv_per_adc",
        "impedance_ohm",
        "preamp_gain",
        "polarity",
        "seed",
        "generator_version",
        "preset",
        "q1_pc",
        "standard_gate_ns",
        "standard_baseline_samples",
    ]:
        assert key in md, key
    assert md["polarity"] == "negative"
    assert md["dt_ns"] == 4.0

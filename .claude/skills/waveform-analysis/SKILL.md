---
name: waveform-analysis
description: Conventions for SiPM and PMT waveform analysis in this lab - baseline, polarity, charge units, gain calibration, selections and the checks a result needs before anyone else sees it. Use when writing or reviewing code that turns digitised waveforms into charge, gain, photoelectron counts or timing.
---

# Waveform analysis conventions

## Read the run metadata first

Every quantity below comes from the run's metadata (`uv run wfkit info <file>`),
never from a constant in the code: `dt_ns`, `mv_per_adc`, `impedance_ohm`,
`preamp_gain`, `polarity`, `standard_gate_ns`, `standard_baseline_samples`.
If a script has a hard-coded value for one of these, treat it as a bug until
shown otherwise.

## Baseline

- Estimate per event from the documented pre-trigger window only. That window
  must end before the earliest possible signal sample.
- Use a robust estimator (median) and keep it in floating point.
- A dark pulse in the baseline window biases the baseline. Flag those events
  with a test on pre-trigger samples only. A cut that looks at pre-trigger
  samples is independent of the light and does not bias the photoelectron count.

## Charge

```
signal = (baseline - waveform)          # for negative polarity
Q [pC] = sum(signal over gate) * mv_per_adc*1e-3 * dt_ns*1e-9 / impedance_ohm / preamp_gain * 1e12
```

- Keep the sign. Noise-only events must give negative charge about half the time.
  `abs()` on a charge is always wrong.
- State the gate in ns and convert with `dt_ns`.

## Gain

- Fit all resolved photoelectron peaks together: means `Q0 + k*G`, widths
  `sqrt(s0^2 + k*s1^2)`. Report G with its fit uncertainty.
- SiPM peak heights are not Poisson (crosstalk). PMT peaks are, which helps
  constrain a broad single-PE response.
- Gain in electrons = G[pC] * 1e-12 / 1.602176634e-19.
- Bright runs have no resolved peaks: reuse a calibration from a low-light run.

## Selections

- Any cut that uses the signal itself (charge, amplitude, peak time inside the
  gate) changes the population you are measuring. Justify it or remove it.
- Report the fraction of events kept.

## Before you call a result done

Run these, and quote the output:

1. Closure against truth where truth exists: `uv run pytest tests/validation -v`
   with `--impl module:function` pointing at the analysis.
2. Pedestal peak at zero within 0.02 photoelectrons.
3. Noise-only events symmetric about zero.
4. Mean true light the same for selected events and all events.
5. Units check by hand on one event: print the ADC sum, then each conversion factor.
6. Write down what the result does not cover (for example, saturation, pile-up
   inside the gate, temperature dependence of gain).

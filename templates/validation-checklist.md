# Validation checklist

Use on any result before you show it to someone else. Tick only what you have
evidence for, and write where the evidence is.

## Units and conversions
- [ ] Every constant traced to a source (metadata, datasheet, measurement). Hard-coded values listed and justified.
- [ ] One event worked through by hand: raw sum, then each conversion factor, then the final number.
- [ ] Result is physically plausible (order of magnitude against a datasheet or a previous measurement).

## Windows and selections
- [ ] Baseline window ends before the earliest signal sample (checked on a plot of the mean waveform).
- [ ] Each cut listed with the fraction of events it removes.
- [ ] Cuts that use the signal itself are justified; otherwise shown not to bias the quantity measured.

## Calculations
- [ ] No silent integer arithmetic, truncation or `abs()` on signed quantities.
- [ ] Fit converges, residuals look structureless, uncertainty reported.
- [ ] Result is stable when a method parameter is varied (bin width, window, fit range, threshold).

## Independent evidence
At least one of these, preferably two:
- [ ] Closure test: analysis recovers known truth on simulated data.
- [ ] Injection test: a known signal added to real data is recovered.
- [ ] Second method: a different technique gives a consistent answer.
- [ ] Invariant: something that must hold (noise symmetric, pedestal at zero, charge linear in light) does hold.

## Sources (for research work)
- [ ] Every factual claim has a source that exists and says what is claimed (checked by opening it).
- [ ] Quoted numbers match the source, including units.

## Provenance
- [ ] Code committed; commit hash recorded.
- [ ] Data file checksums recorded.
- [ ] Parts written by an agent are identified, and a person has read them.

## Limitations
- [ ] Written down, specifically, in the handoff note.

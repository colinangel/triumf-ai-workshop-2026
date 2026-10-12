"""Does the analysis recover what the detector simulation actually did?

Each test states one physical expectation and compares the analysis to the
generator's ground truth. Tolerances are set from the statistical precision of
a correct analysis on these datasets, with margin; they are not tuned to pass.

Run:   uv run pytest tests/validation -v
Other: uv run pytest tests/validation -v --impl mypackage.analysis:analyze
"""

import numpy as np
import pytest

pytestmark = pytest.mark.validation


def _clean_zero_pe(case):
    """Events with no photoelectron anywhere from record start to 400 ns after the gate."""
    pe = case.pe
    busy = pe.loc[pe["t_ns"] < case.cfg.standard_gate_ns[1] + 400, "event"].unique()
    return ~np.isin(case.truth["event"].to_numpy(), busy)


# --- charge scale and offset -------------------------------------------------


def test_charge_scale_matches_truth(lowlight):
    """Per-event charge, divided by true charge in the gate, should be 1."""
    t = lowlight.truth
    m = lowlight.sel & (t["q_gate_true_pc"].to_numpy() > 0.5 * lowlight.q1)
    ratio = np.median(lowlight.q[m] / t["q_gate_true_pc"].to_numpy()[m])
    assert ratio == pytest.approx(1.0, abs=0.01), f"reconstructed/true charge = {ratio:.4f}"


def test_charge_has_no_offset(lowlight):
    """Mean residual (reco - true) on selected events should be zero to 0.01 PE."""
    resid = (lowlight.q - lowlight.truth["q_gate_true_pc"].to_numpy())[lowlight.sel] / lowlight.q1
    se = resid.std() / np.sqrt(resid.size)
    assert abs(resid.mean()) < max(0.01, 4 * se), f"mean residual = {resid.mean():+.4f} PE (stat. error {se:.4f})"


def test_charge_scale_holds_at_high_light(highlight):
    """Same scale check where pulses are ~10x larger: catches amplitude-dependent bias."""
    t = highlight.truth
    m = highlight.sel & (t["q_gate_true_pc"].to_numpy() > 2 * highlight.q1)
    ratio = np.median(highlight.q[m] / t["q_gate_true_pc"].to_numpy()[m])
    assert ratio == pytest.approx(1.0, abs=0.01), f"reconstructed/true charge = {ratio:.4f}"


def test_noise_events_are_symmetric_about_zero(lowlight):
    """With no light, charge is pure noise and should be negative about half the time."""
    zero = _clean_zero_pe(lowlight)
    assert zero.sum() > 500, "not enough clean zero-PE events to test"
    frac_neg = np.mean(lowlight.q[zero] < 0)
    assert 0.40 < frac_neg < 0.60, f"fraction of noise-only events with negative charge = {frac_neg:.3f}"


# --- calibration -------------------------------------------------------------


def test_gain_matches_truth(lowlight):
    expected = lowlight.finger_spacing_pc
    got = lowlight.r["gain_pc"]
    assert got == pytest.approx(expected, rel=0.015), f"gain = {got:.5f} pC/PE, truth {expected:.5f} ({got / expected - 1:+.2%})"


def test_gain_in_electrons_is_consistent(lowlight):
    e = 1.602176634e-19
    assert lowlight.r["gain"] == pytest.approx(lowlight.r["gain_pc"] * 1e-12 / e, rel=1e-6)


def test_pedestal_peak_is_at_zero(lowlight):
    ped = lowlight.r["pedestal_pc"] / lowlight.q1
    assert abs(ped) < 0.02, f"pedestal at {ped:+.4f} PE"


# --- selection ---------------------------------------------------------------


def test_selection_keeps_most_events(lowlight):
    assert lowlight.sel.mean() > 0.5, f"only {lowlight.sel.mean():.1%} of events selected"


def test_selection_does_not_bias_the_light(lowlight):
    """Selected events should see the same light as all events (cuts must not depend on the signal)."""
    n = lowlight.truth["n_primary"].to_numpy()
    sel, mu = n[lowlight.sel], n.mean()
    se = np.sqrt(mu / sel.size)
    assert abs(sel.mean() - mu) < 4 * se, f"mean true primary PE: selected {sel.mean():.4f}, all events {mu:.4f}"


def test_mean_photoelectrons_in_gate(lowlight):
    """Mean PE per trigger, compared to the truth over ALL triggers."""
    truth = lowlight.truth["q_gate_true_pc"].mean() / lowlight.finger_spacing_pc
    got = lowlight.r["mean_npe_in_gate"]
    assert got == pytest.approx(truth, rel=0.02), f"mean PE in gate = {got:.4f}, truth {truth:.4f} ({got / truth - 1:+.2%})"


# --- stretch -----------------------------------------------------------------


@pytest.mark.advanced
def test_pmt_gain_matches_truth(pmt):
    """PMT single-PE peak is broad and sits close to the pedestal; needs a different fit model."""
    expected = pmt.finger_spacing_pc
    got = pmt.r["gain_pc"]
    assert got == pytest.approx(expected, rel=0.05), f"PMT gain = {got:.4f} pC/PE, truth {expected:.4f} ({got / expected - 1:+.2%})"

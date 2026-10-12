"""Pulse templates must have unit area so that charge bookkeeping is exact.

These tests pin down the contract the generator relies on: a template sampled
at dt_ns, summed and multiplied by dt_ns, equals the fraction of the pulse
that falls inside the record. If that is wrong, every truth charge is wrong.
"""

import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from wfkit.pulses import PMTPulse, SiPMPulse


@pytest.mark.parametrize("pulse", [SiPMPulse(rise_ns=3.0, fall_ns=45.0), PMTPulse(scale_ns=8.0, width=0.35)])
def test_continuous_shape_integrates_to_one(pulse):
    t = np.linspace(-50, 5000, 2_000_001)
    area = np.trapezoid(pulse.shape(t), t)
    assert area == pytest.approx(1.0, rel=1e-4)


@pytest.mark.parametrize("pulse", [SiPMPulse(rise_ns=3.0, fall_ns=45.0), PMTPulse(scale_ns=8.0, width=0.35)])
def test_cdf_matches_numerical_integral(pulse):
    t = np.linspace(0, 400, 400_001)
    numeric = np.trapezoid(pulse.shape(t), t)
    assert pulse.cdf(400.0) - pulse.cdf(0.0) == pytest.approx(numeric, rel=1e-4)


@settings(max_examples=40, deadline=None)
@given(
    rise=st.floats(0.5, 10.0),
    fall=st.floats(15.0, 120.0),
    t0=st.floats(100.0, 300.0),
)
def test_sampled_sipm_template_conserves_area(rise, fall, t0):
    """Sampling must not lose or invent charge, whatever the sub-sample phase."""
    pulse = SiPMPulse(rise_ns=rise, fall_ns=fall)
    dt = 4.0
    n = 1024
    sampled = pulse.sample(t0_ns=t0, dt_ns=dt, n_samples=n)
    expected = pulse.cdf(n * dt - t0) - pulse.cdf(-t0)
    assert sampled.sum() * dt == pytest.approx(expected, rel=2e-3)


def test_pulse_before_start_is_zero():
    pulse = SiPMPulse(rise_ns=3.0, fall_ns=45.0)
    assert np.all(pulse.shape(np.array([-10.0, -1e-9])) == 0.0)


def test_sipm_rejects_unphysical_time_constants():
    with pytest.raises(ValueError):
        SiPMPulse(rise_ns=50.0, fall_ns=10.0)

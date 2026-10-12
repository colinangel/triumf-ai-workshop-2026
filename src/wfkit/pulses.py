"""Single-photoelectron pulse shapes.

Every shape is normalised to unit area in nanoseconds, so a pulse multiplied by
a charge gives a current-like signal whose integral is that charge. Sampling
uses the exact cumulative distribution over each sample interval, which keeps
charge conserved regardless of where the pulse falls within a sample.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

import numpy as np
from scipy.special import erf


class Pulse(Protocol):
    def shape(self, t: np.ndarray) -> np.ndarray: ...
    def cdf(self, t: np.ndarray) -> np.ndarray: ...


@dataclass(frozen=True)
class SiPMPulse:
    """Difference of exponentials: fast avalanche rise, slow recharge fall."""

    rise_ns: float
    fall_ns: float

    def __post_init__(self) -> None:
        if not (0 < self.rise_ns < self.fall_ns):
            raise ValueError("SiPM pulse needs 0 < rise_ns < fall_ns")

    def shape(self, t):
        t = np.asarray(t, dtype=np.float64)
        tp = np.clip(t, 0.0, None)
        v = (np.exp(-tp / self.fall_ns) - np.exp(-tp / self.rise_ns)) / (self.fall_ns - self.rise_ns)
        return np.where(t >= 0, v, 0.0)

    def cdf(self, t):
        t = np.asarray(t, dtype=np.float64)
        tp = np.clip(t, 0.0, None)
        a, b = self.fall_ns, self.rise_ns
        v = 1.0 - (a * np.exp(-tp / a) - b * np.exp(-tp / b)) / (a - b)
        return np.where(t >= 0, v, 0.0)

    def sample(self, t0_ns: float, dt_ns: float, n_samples: int) -> np.ndarray:
        return sample_pulses(self, np.array([t0_ns]), dt_ns, n_samples)[0]


@dataclass(frozen=True)
class PMTPulse:
    """Log-normal pulse, a common empirical model of PMT anode signals."""

    scale_ns: float
    width: float  # dimensionless log-normal sigma

    def __post_init__(self) -> None:
        if self.scale_ns <= 0 or self.width <= 0:
            raise ValueError("PMT pulse needs positive scale_ns and width")

    def shape(self, t):
        t = np.asarray(t, dtype=np.float64)
        tp = np.where(t > 0, t, 1.0)
        v = np.exp(-(np.log(tp / self.scale_ns) ** 2) / (2 * self.width**2)) / (tp * self.width * np.sqrt(2 * np.pi))
        return np.where(t > 0, v, 0.0)

    def cdf(self, t):
        t = np.asarray(t, dtype=np.float64)
        tp = np.where(t > 0, t, 1.0)
        v = 0.5 * (1.0 + erf(np.log(tp / self.scale_ns) / (self.width * np.sqrt(2))))
        return np.where(t > 0, v, 0.0)

    def sample(self, t0_ns: float, dt_ns: float, n_samples: int) -> np.ndarray:
        return sample_pulses(self, np.array([t0_ns]), dt_ns, n_samples)[0]


def sample_pulses(pulse: Pulse, t0_ns: np.ndarray, dt_ns: float, n_samples: int) -> np.ndarray:
    """Return an (n_pulses, n_samples) array of per-sample mean amplitudes.

    Sample i covers [i*dt, (i+1)*dt). Its value is the pulse area inside that
    interval divided by dt, so sum(row) * dt equals the area inside the record.
    """
    t0 = np.asarray(t0_ns, dtype=np.float64)[:, None]
    edges = np.arange(n_samples + 1, dtype=np.float64)[None, :] * dt_ns
    return np.diff(pulse.cdf(edges - t0), axis=1) / dt_ns

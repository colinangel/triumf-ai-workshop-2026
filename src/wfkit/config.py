"""Run configuration for the synthetic detector, with workshop presets.

All quantities carry their unit in the field name. Charges are at the sensor
(before the preamplifier), in picocoulombs.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from wfkit.pulses import PMTPulse, SiPMPulse

ELEMENTARY_CHARGE_C = 1.602176634e-19  # exact, SI 2019


@dataclass(frozen=True)
class DigitizerConfig:
    model: str = "V1725-like, 250 MS/s, 14-bit, 2 Vpp"
    dt_ns: float = 4.0
    n_samples: int = 512
    trigger_sample: int = 128
    adc_bits: int = 14
    mv_per_adc: float = 2000.0 / 2**14
    pedestal_adc: float = 15000.0
    noise_adc: float = 3.0
    pedestal_drift_adc: float = 2.0  # slow drift amplitude across the run
    pedestal_jitter_adc: float = 0.5  # event-to-event baseline wander
    impedance_ohm: float = 50.0

    @property
    def adc_max(self) -> int:
        return 2**self.adc_bits - 1


@dataclass(frozen=True)
class SensorConfig:
    kind: str  # "sipm" or "pmt"
    pulse: SiPMPulse | PMTPulse
    gain: float
    gain_spread: float  # relative sigma of single-PE charge
    preamp_gain: float
    crosstalk_prob: float = 0.0
    afterpulse_prob: float = 0.0
    afterpulse_model: str = "exponential"  # "exponential" (SiPM) or "gaussian" (PMT)
    afterpulse_delay_ns: float = 60.0  # mean delay
    afterpulse_delay_sigma_ns: float = 0.0  # gaussian model only
    recovery_tau_ns: float = 0.0  # SiPM cell recharge; scales afterpulse charge
    dark_rate_hz: float = 0.0
    transit_jitter_ns: float = 0.0


@dataclass(frozen=True)
class LightConfig:
    mu: float  # mean primary photoelectrons per event
    offset_ns: float = 20.0  # light arrival after the trigger time
    decay_ns: float = 0.0  # 0 = prompt flash (LED); >0 = exponential emission


@dataclass(frozen=True)
class RunConfig:
    name: str
    description: str
    digitizer: DigitizerConfig
    sensor: SensorConfig
    light: LightConfig
    standard_gate_ns: tuple[float, float]
    standard_baseline_samples: tuple[int, int] = (0, 100)
    channel_delays_ns: tuple[float, ...] = (0.0,)
    default_events: int = 20_000
    default_seed: int = 2026
    extra: dict = field(default_factory=dict)

    @property
    def n_channels(self) -> int:
        return len(self.channel_delays_ns)

    @property
    def trigger_time_ns(self) -> float:
        return self.digitizer.trigger_sample * self.digitizer.dt_ns

    @property
    def q1_pc(self) -> float:
        """Mean single-photoelectron charge at the sensor, pC."""
        return self.sensor.gain * ELEMENTARY_CHARGE_C * 1e12

    @property
    def adc_samples_to_pc(self) -> float:
        """Sensor charge (pC) represented by one ADC count held for one sample."""
        d = self.digitizer
        volts_seconds = d.mv_per_adc * 1e-3 * d.dt_ns * 1e-9
        return volts_seconds / d.impedance_ohm / self.sensor.preamp_gain * 1e12


SIPM = SensorConfig(
    kind="sipm",
    pulse=SiPMPulse(rise_ns=3.0, fall_ns=45.0),
    gain=1.2e6,
    gain_spread=0.08,
    preamp_gain=30.0,
    crosstalk_prob=0.12,
    afterpulse_prob=0.04,
    afterpulse_model="exponential",
    afterpulse_delay_ns=60.0,
    recovery_tau_ns=20.0,
    dark_rate_hz=400e3,
    transit_jitter_ns=0.15,
)

PMT = SensorConfig(
    kind="pmt",
    pulse=PMTPulse(scale_ns=8.0, width=0.35),
    gain=1.0e7,
    gain_spread=0.35,
    preamp_gain=1.0,
    afterpulse_prob=0.02,
    afterpulse_model="gaussian",
    afterpulse_delay_ns=900.0,
    afterpulse_delay_sigma_ns=100.0,
    dark_rate_hz=2e3,
    transit_jitter_ns=1.2,
)

DIGI = DigitizerConfig()

PRESETS: dict[str, RunConfig] = {
    "sipm_lowlight": RunConfig(
        name="sipm_lowlight",
        description="SiPM under pulsed LED, low intensity: resolved photoelectron peaks for gain calibration.",
        digitizer=DIGI,
        sensor=SIPM,
        light=LightConfig(mu=1.5),
        standard_gate_ns=(480.0, 800.0),
        default_seed=1601,
    ),
    "sipm_highlight": RunConfig(
        name="sipm_highlight",
        description="Same SiPM, higher LED intensity: linearity and mean photoelectron studies.",
        digitizer=DIGI,
        sensor=SIPM,
        light=LightConfig(mu=12.0),
        standard_gate_ns=(480.0, 800.0),
        default_seed=1602,
    ),
    "sipm_dark": RunConfig(
        name="sipm_dark",
        description="Same SiPM, random trigger with the LED off: dark count rate, crosstalk, afterpulsing.",
        digitizer=DIGI,
        sensor=SIPM,
        light=LightConfig(mu=0.0),
        standard_gate_ns=(480.0, 800.0),
        default_seed=1603,
    ),
    "pmt_spe": RunConfig(
        name="pmt_spe",
        description="PMT single-photoelectron run: broad SPE response and late afterpulses.",
        digitizer=DIGI,
        sensor=PMT,
        light=LightConfig(mu=0.3),
        standard_gate_ns=(520.0, 580.0),
        default_seed=1604,
    ),
    "coincidence": RunConfig(
        name="coincidence",
        description="Two SiPMs viewing one scintillator: relative timing with a known cable delay.",
        digitizer=DIGI,
        sensor=SIPM,
        light=LightConfig(mu=25.0, decay_ns=2.0),
        standard_gate_ns=(480.0, 800.0),
        channel_delays_ns=(0.0, 3.2),
        default_events=10_000,
        default_seed=1605,
    ),
}

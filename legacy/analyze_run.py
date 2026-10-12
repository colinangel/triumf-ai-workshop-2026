#!/usr/bin/env python
# analyze_run.py  -- SiPM gain / charge analysis
#
# Originally written for the 2022 LED test stand, updated a few times since.
# Usage:  python legacy/analyze_run.py data/sipm_lowlight.parquet
#
# Makes charge_spectrum.png and prints gain + mean number of PE.
# Ask around if something looks off, most of the constants were tuned by hand.

import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pyarrow.parquet as pq
from scipy.signal import find_peaks

DT = 2.0  # ns per sample (V1730)
R = 50.0  # termination, ohm
PREAMP = 30.0  # amplifier gain
MV_PER_ADC = 2000.0 / 16384  # 14 bit, 2 Vpp
E_CHARGE = 1.602176634e-19

TRIG = 128  # trigger sample
BL_END = 135  # baseline uses everything before the pulse
GATE = (120, 200)  # integration window, samples
NOISE_CUT = 0.05  # pC, removes pedestal / noise events

DEBUG = True


def load(path):
    t = pq.read_table(path)
    n = len(t)
    wf = t["wf_ch0"].combine_chunks().flatten().to_numpy().reshape(n, -1)
    if DEBUG:
        print("loaded", n, "events,", wf.shape[1], "samples each")
    return t["event"].to_numpy(), wf


def charge(wf):
    # baseline
    baseline = int(np.mean(wf[0:BL_END]))
    # subtract and integrate
    s = 0
    for i in range(GATE[0], GATE[1]):
        s = s + (baseline - wf[i])
    q = s * MV_PER_ADC * 1e-3 * DT * 1e-9 / R / PREAMP * 1e12  # pC
    return abs(q)  # abs so polarity does not matter


def find_gain(q):
    h, edges = np.histogram(q, bins=200, range=(0, 1.0))
    centres = 0.5 * (edges[1:] + edges[:-1])
    hs = np.convolve(h, np.ones(3) / 3, mode="same")
    peaks, _ = find_peaks(hs, prominence=hs.max() * 0.02, distance=5)
    if DEBUG:
        print("peaks at", centres[peaks][:6])
    pos = centres[peaks][:4]
    gain_pc = np.mean(np.diff(pos))
    return pos[0], gain_pc, h, centres


def analyze(path):
    event, wf = load(path)
    q = np.zeros(len(wf))
    for i in range(len(wf)):
        q[i] = charge(wf[i].astype(np.int64))
        if DEBUG and i % 5000 == 0:
            print("event", i, "q =", q[i])
    ped, gain_pc, h, centres = find_gain(q)
    good = q > NOISE_CUT
    mean_npe = np.mean(q[good]) / gain_pc
    gain = gain_pc * 1e-12 / E_CHARGE
    return {
        "event": event,
        "charge_pc": q,
        "selected": good,
        "pedestal_pc": ped,
        "gain_pc": gain_pc,
        "gain": gain,
        "gain_err": float("nan"),
        "mean_npe_in_gate": mean_npe,
        "_hist": (h, centres),
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: analyze_run.py file.parquet")
        sys.exit(1)
    r = analyze(sys.argv[1])
    print("pedestal (pC):", r["pedestal_pc"])
    print("gain (pC/PE):", r["gain_pc"])
    print("gain:", "%.3e" % r["gain"])
    print("mean npe:", r["mean_npe_in_gate"])
    h, c = r["_hist"]
    plt.step(c, h, where="mid")
    plt.xlabel("charge (pC)")
    plt.ylabel("events")
    plt.yscale("log")
    plt.title(sys.argv[1])
    plt.savefig("charge_spectrum.png", dpi=120)
    print("saved charge_spectrum.png")

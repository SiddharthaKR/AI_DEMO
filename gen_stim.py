#!/usr/bin/env python3
"""One-time stimulus generator: PRBS7 NRZ, raised-cosine pulse, OSR=2,
optional fractional delay TAU_TRUE_UI, quantized to UNSIGNED 6-bit (0..63).
Midscale is exactly 32 (the RTL and C++ both subtract 32)."""
import numpy as np, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parent
P = {}
for line in (ROOT / "params.txt").read_text().splitlines():
    line = line.split("#")[0].strip()
    if "=" in line:
        k, v = line.split("=", 1); P[k.strip()] = v.strip()

OSR, BETA, SPAN = 2, 0.5, 8
n_sym = int(P["N_SYM"]) + 64                       # margin for the NCO pointer
tau_true = float(P["TAU_TRUE_UI"]) if P.get("TAU_TRUE_UI") else 0.0

# PRBS7: x^7 + x^6 + 1
reg, bits = 0x7F, []
for _ in range(n_sym):
    b = ((reg >> 6) ^ (reg >> 5)) & 1
    reg = ((reg << 1) | b) & 0x7F
    bits.append(b)
sym = 2.0 * np.array(bits) - 1.0

def rc(t):                                         # raised cosine, t in UI
    t = np.asarray(t, float)
    den = 1.0 - (2 * BETA * t) ** 2
    out = np.sinc(t) * np.cos(np.pi * BETA * t) / np.where(np.abs(den) < 1e-9, 1.0, den)
    return np.where(np.abs(den) < 1e-9, np.pi / 4 * np.sinc(1 / (2 * BETA)), out)

t = np.arange(n_sym * OSR) / OSR                   # sample times in UI
s = np.zeros_like(t)
for k in range(n_sym):
    m = np.abs(t - k - tau_true) <= SPAN
    s[m] += sym[k] * rc(t[m] - k - tau_true)

x = np.clip(np.round(32 + 26 * s / np.max(np.abs(s))), 0, 63).astype(int)
out = ROOT / "data" / "stim.txt"
out.write_text("\n".join(map(str, x)) + "\n")
print(f"wrote {out} ({len(x)} samples, tau_true={tau_true} UI)")

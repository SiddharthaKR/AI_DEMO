#!/usr/bin/env python3
"""verify_tau.py - THE tool of the ted-verify skill.

Runs the SAME stimulus through
  (1) RTL  : iverilog + rtl/tb_ted.v + rtl/ted_toy[_broken].v
  (2) C++  : g++ model/ted_toy.cpp (float golden model)
then compares the converged tau (circular mean of the last 10 % of updates, mod 1 UI).

usage:  python .opencode/skills/ted-verify/scripts/verify_tau.py [--variant good|broken] [--stim FILE]
prints: first line 'VERDICT: ...', then a JSON block (also saved to out/verify_result.json).
"""
import argparse, json, pathlib, shutil, subprocess, sys
import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[4]       # repo root
OUT = ROOT / "out"
OSR, TAU_FRAC_BITS = 2, 16                                # fixed by the RTL
TOL_UI, CONV_STD_UI, WINDOW_FRAC = 0.02, 0.02, 0.10


def load_params():
    p = {}
    for line in (ROOT / "params.txt").read_text().splitlines():
        line = line.split("#")[0].strip()
        if "=" in line:
            k, v = line.split("=", 1)
            p[k.strip()] = v.strip()
    return p


def run(cmd):
    r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"{' '.join(cmd)}\n{r.stderr.strip() or r.stdout.strip()}")
    return r.stdout


def wrap(d):                                  # circular difference in (-0.5, 0.5]
    return (d + 0.5) % 1.0 - 0.5


def converged(tau_ui):
    n = max(1, int(len(tau_ui) * WINDOW_FRAC))
    w = tau_ui[-n:]
    mean = (np.angle(np.mean(np.exp(2j * np.pi * w))) / (2 * np.pi)) % 1.0
    std = float(np.std(wrap(w - mean)))
    return float(mean), std, n


def plot(rtl, cpp, m_rtl, m_cpp, tau_true, n_win, verdict, variant):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(9, 4))
    k = np.arange(max(len(rtl), len(cpp)))
    ax.axvspan(len(rtl) - n_win, len(rtl), color="0.9", label="convergence window (last 10%)")
    ax.plot(k[:len(cpp)], cpp, lw=1.2, label=f"C++ float  -> {m_cpp:.4f} UI")
    ax.plot(k[:len(rtl)], rtl, lw=1.0, alpha=0.8, label=f"RTL ({variant}) -> {m_rtl:.4f} UI")
    if tau_true is not None:
        ax.axhline(tau_true, ls=":", c="k", label=f"tau_true = {tau_true} UI")
    ax.set_ylim(0, 1); ax.set_xlabel("symbol k"); ax.set_ylabel("tau [UI], mod 1")
    ax.set_title(f"TED tau convergence: RTL vs C++   [{verdict}]")
    ax.legend(loc="upper right", fontsize=8); ax.grid(alpha=0.3)
    fig.tight_layout()
    path = OUT / "tau_trace.png"
    fig.savefig(path, dpi=120); plt.close(fig)
    return path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--variant", choices=["good", "broken"], default="good")
    ap.add_argument("--stim", default="data/stim.txt")
    a = ap.parse_args()
    OUT.mkdir(exist_ok=True)
    res = {"variant": a.variant, "stim": a.stim}

    try:
        for exe in ("iverilog", "vvp", "g++"):
            if not shutil.which(exe):
                raise RuntimeError(f"'{exe}' not found on PATH")
        P = load_params()
        n_sym, kp, ki = int(P["N_SYM"]), int(P["KP_SHIFT"]), int(P["KI_SHIFT"])
        tau0_s = (float(P.get("TAU0_UI") or 0.0) % 1.0) * OSR          # UI -> samples
        tau0_q = int(round(tau0_s * (1 << TAU_FRAC_BITS)))
        tau_true = float(P["TAU_TRUE_UI"]) if P.get("TAU_TRUE_UI") else None

        rtl_src = "rtl/ted_toy.v" if a.variant == "good" else "rtl/ted_toy_broken.v"
        run(["iverilog", "-g2005", "-o", "out/sim.vvp",
             "-P", f"tb_ted.N_SYM={n_sym}", "-P", f"tb_ted.KP_SHIFT={kp}",
             "-P", f"tb_ted.KI_SHIFT={ki}", "-P", f"tb_ted.TAU0_Q={tau0_q}",
             "rtl/tb_ted.v", rtl_src])
        run(["vvp", "-n", "out/sim.vvp", f"+STIM={a.stim}", "+OUT=out/rtl_tau.txt"])
        run(["g++", "-O2", "-std=c++17", "model/ted_toy.cpp", "-o", "out/ted_cpp"])
        run([str(OUT / "ted_cpp"), a.stim, "out/cpp_tau.txt",
             str(n_sym), str(kp), str(ki), f"{tau0_s:.9f}"])

        rtl = (np.loadtxt(OUT / "rtl_tau.txt") / (1 << TAU_FRAC_BITS) / OSR) % 1.0
        cpp = (np.loadtxt(OUT / "cpp_tau.txt") / OSR) % 1.0
        m_rtl, s_rtl, n_win = converged(rtl)
        m_cpp, s_cpp, _ = converged(cpp)
        delta = round(float(wrap(m_rtl - m_cpp)), 6) + 0.0

        reasons = []
        if s_rtl >= CONV_STD_UI: reasons.append(f"RTL not converged (std {s_rtl:.4f} >= {CONV_STD_UI} UI)")
        if s_cpp >= CONV_STD_UI: reasons.append(f"C++ not converged (std {s_cpp:.4f} >= {CONV_STD_UI} UI)")
        if abs(delta) >= TOL_UI: reasons.append(f"RTL vs C++ mismatch |delta| = {abs(delta):.4f} >= {TOL_UI} UI")
        gt = None
        if tau_true is not None:
            e_r, e_c = float(wrap(m_rtl - tau_true)), float(wrap(m_cpp - tau_true))
            gt = {"tau_true_ui": tau_true, "rtl_err_ui": round(e_r, 5), "cpp_err_ui": round(e_c, 5),
                  "pass": abs(e_r) < TOL_UI and abs(e_c) < TOL_UI}
            if not gt["pass"]: reasons.append(f"ground truth: RTL err {e_r:+.4f}, C++ err {e_c:+.4f} UI")

        verdict = "PASS" if not reasons else "FAIL"
        res.update({
            "verdict": verdict,
            "tau_rtl_ui": round(m_rtl, 5), "tau_cpp_ui": round(m_cpp, 5),
            "delta_ui": round(delta, 5) + 0.0, "tol_ui": TOL_UI,
            "rtl_std_ui": round(s_rtl, 5), "cpp_std_ui": round(s_cpp, 5),
            "rtl_converged": s_rtl < CONV_STD_UI, "cpp_converged": s_cpp < CONV_STD_UI,
            "ground_truth": gt, "n_updates": int(len(rtl)), "window_updates": n_win,
            "reasons": reasons,
        })
        res["plot"] = str(plot(rtl, cpp, m_rtl, m_cpp, tau_true, n_win, verdict, a.variant).relative_to(ROOT))
        head = (f"VERDICT: {verdict} | RTL {m_rtl:.4f} UI | C++ {m_cpp:.4f} UI | "
                f"delta {delta:+.4f} UI (tol {TOL_UI})")
    except Exception as ex:                                    # never let the model guess
        res.update({"verdict": "ERROR", "error": str(ex)})
        head = f"VERDICT: ERROR | {str(ex).splitlines()[0]}"

    (OUT / "verify_result.json").write_text(json.dumps(res, indent=2))
    print(head)
    print(json.dumps(res, indent=2))
    return 0 if res["verdict"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())

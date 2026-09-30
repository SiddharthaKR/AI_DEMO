---
name: ted-verify
description: Verify the TED / CDR RTL against the C++ golden model by comparing converged tau. Use this skill whenever the user asks to verify, check, compare, or test the RTL vs C++ / model / simulation, asks if tau converged or matches, asks whether the RTL is correct, or mentions iverilog, tau, TED, CDR, or convergence. Also use it for the broken demo variant.
---

# ted-verify

## The tool
One command runs everything (RTL sim, C++ model, comparison, plot):

    python .opencode/skills/ted-verify/scripts/verify_tau.py [--variant good|broken] [--stim FILE]

- `--variant good` (default) uses `rtl/ted_toy.v`
- `--variant broken` uses `rtl/ted_toy_broken.v` (demo bug)
- `--stim` defaults to `data/stim.txt`

## Workflow
1. Run the tool. Choose `--variant broken` only if the user asks for the broken / buggy version.
2. Read the first output line `VERDICT: ...` and the JSON below it.
3. Reply in this format:
   - **Verdict:** PASS / FAIL / ERROR
   - **Numbers:** tau_rtl_ui, tau_cpp_ui, delta_ui (tol_ui), and ground_truth if not null
   - **Why:** 1-2 sentences using the `reasons` list (FAIL) or `error` (ERROR)
   - **Plot:** the `plot` path

## How to explain a FAIL (use only what the JSON shows)
- delta about 0.5 UI and RTL std high -> the loop locked on the wrong zero crossing of the S-curve. The usual cause is a flipped TED error sign.
- Not converged but delta small -> the loop is still noisy; the gains may be too high.
- Both RTL and C++ miss ground truth -> the stimulus or the params disagree with tau_true, not the RTL.

## Do not
- Do not edit RTL or C++ to "fix" a FAIL unless the user asks.
- Do not compute tau or delta yourself. Only quote the tool's numbers.

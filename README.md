# ted-demo — local AI (opencode + Gemma) verifies RTL vs C++

1 skill (`ted-verify`) + 1 tool (`verify_tau.py`): the same stimulus goes through the
iverilog RTL and a float C++ model, and the converged tau is compared (mod 1 UI).

## Requirements
iverilog (>= 11), g++, python3 with numpy + matplotlib, opencode pointed at your Gemma endpoint.

## Setup (once)
    python gen_stim.py                                        # writes data/stim.txt from params.txt
    python .opencode/skills/ted-verify/scripts/verify_tau.py  # sanity check: expect PASS

## Files
| File | Role |
|---|---|
| `AGENTS.md` | always-loaded project rules |
| `.opencode/skills/ted-verify/SKILL.md` | on-demand playbook: when/how to verify |
| `.opencode/skills/ted-verify/scripts/verify_tau.py` | THE tool: build, run, compare, plot |
| `rtl/ted_toy.v`, `rtl/tb_ted.v` | Verilog-2005 loop + testbench |
| `rtl/ted_toy_broken.v` | demo bug: one line, TED sign flipped |
| `model/ted_toy.cpp` | float golden model |
| `params.txt` | N_SYM, KP_SHIFT, KI_SHIFT, TAU0_UI, TAU_TRUE_UI (empty = skip ground truth) |
| `gen_stim.py` | one-time PRBS7 / raised-cosine / OSR 2 stimulus, unsigned 6-bit |

## Demo script (3 prompts)
1. "Verify the TED RTL against the C++ model."         -> PASS, both ~0.30 UI
2. "Now check the broken RTL variant."                 -> FAIL, delta ~0.49 UI, wrong lock point
3. "What exactly is different in the broken file?"      -> agent diffs the two .v files: one line, sign flip

Open `out/tau_trace.png` after prompts 1 and 2 to show the audience.

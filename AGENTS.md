# ted-demo — project rules (always loaded)

## What this repo is
A toy Mueller-Muller CDR loop (TED + PI + NCO, OSR = 2) implemented twice:
- `rtl/ted_toy.v`   : fixed-point Verilog (tau = Q4.16 samples), simulated with iverilog
- `model/ted_toy.cpp`: float C++ golden model
Both read the same input `data/stim.txt` (unsigned 6-bit, one sample per line).
`rtl/ted_toy_broken.v` is a deliberate demo bug (flipped TED sign).
Shared settings live in `params.txt`.

## Rules
- NEVER edit files in `rtl/`, `model/`, `data/`, or `params.txt` unless the user explicitly asks.
- For anything about RTL vs C++ results, tau, or convergence: load the `ted-verify` skill and run its tool.
- Never state a tau value, a difference, or a PASS/FAIL you did not read from tool output.
- Tau is reported in UI, modulo 1.

## Language
Reply in the language of the user's message (English or Japanese).
Never translate file names, signal names, flags, or numbers.

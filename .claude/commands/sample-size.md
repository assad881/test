---
description: حساب حجم العينة مع نص Methods جاهز
argument-hint: <study design + parameters>
---
Calculate the sample size for: $ARGUMENTS

1. Identify the design and the right formula (single proportion/Cochran ± FPC, two proportions, two
   means, correlation, logistic EPV, diagnostic accuracy (Buderer), or ask if unclear).
2. Run `python3 assistant/engine/sample_size.py ...` (see `--help`) — do not compute by hand.
3. Show: inputs and their justification (cite where p/SD should come from: pilot or literature),
   result, non-response inflation, design effect if cluster sampling.
4. Give a **Methods paragraph** ready to paste, and a sensitivity table (e.g. margin 4/5/6%,
   p 0.3/0.5).

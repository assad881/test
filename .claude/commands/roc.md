---
description: تحليل منحنى ROC — AUC، نقطة القطع المثلى (Youden)، الحساسية والنوعية، ومقارنة DeLong
argument-hint: <data.xlsx> <outcome> <marker(s)> [event] [ar]
---
Run a ROC / diagnostic-accuracy analysis for: $ARGUMENTS

1. Identify the binary reference standard (outcome + event value) and the marker(s). Check event count
   (≥ 2 per class; warn if prevalence < 10% or events < 30 — CIs will be wide).
2. Set direction per marker: "higher" if higher values indicate the event (default), "lower" otherwise.
   If AUC < 0.5 the engine warns — flip the direction rather than reporting 1 − AUC silently.
3. Write a plan (reuse `assistant/clients/<project>/plan.json` if it exists) with:
   `"roc": {"outcome": ..., "event": ..., "markers": [...], "direction": {"X": "lower"}, "include_logistic_model": false}`
   and `"languages": ["en"]` or `["en","ar"]` if Arabic was requested.
4. Run `python3 assistant/engine/auto_analysis.py <plan.json>`.
5. Report: AUC (95% CI, DeLong), p, interpretation (Hosmer–Lemeshow), Youden cut-off with Se/Sp
   (Wilson CI), PPV/NPV (state they depend on prevalence), LR+/LR−, DeLong pairwise comparison,
   ROC figure. Mention STARD items if it is a diagnostic accuracy study. Give SPSS `ROC` syntax
   from `<project>_syntax.sps`.

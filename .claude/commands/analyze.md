---
description: تحليل كامل آلي — استبيان + بيانات Excel → تقرير Word وجداول وSPSS syntax
argument-hint: <data.xlsx> [questionnaire.docx]
---
Run the AsaadStat Automated Research Analysis System on: $ARGUMENTS

1. **Inspect the data** (pandas): shape, column names, types, missing %, out-of-range codes, duplicates
   by ID. If a questionnaire (Word/PDF) is given, read it to map items → domains, correct answers, and
   reverse-worded items. Report data-quality issues in a short table before analysing.
2. **Build the plan**: copy `assistant/templates/analysis_plan_template.json` to
   `assistant/clients/<project>/plan.json` and fill in demographics, scales (items, item_min/max,
   reverse_items, cut-offs), group_comparisons, associations, correlations, logistic (outcome/event/
   predictors/reference), and `roc` if a marker/score must discriminate a binary outcome. Prefer
   theory-driven predictors; keep EPV ≥ 10. Use `recode` for text→code mapping (e.g. correct/incorrect → 1/0).
   **Language**: `"languages": ["en"]` by default; add `"ar"` when Asaad asks for an Arabic report (or the
   client/decision-makers need Arabic). For Arabic also fill `title_ar`, `var_labels` ({"en":..,"ar":..})
   and `value_labels_ar` for study-specific categories (common ones like Male/Female/Yes/No are built in).
3. **Show the plan** to Asaad as a compact table (objective → variables → test) and state any
   assumptions (cut-offs, references). Proceed unless something is ambiguous enough to change results.
4. **Run**: `python3 assistant/engine/auto_analysis.py assistant/clients/<project>/plan.json`
5. **Review** `<project>_summary.md` critically: assumption warnings, sparse cells, low α items,
   extreme ORs, EPV. Fix the plan and rerun if needed.
6. **Deliver**: list output files (report.docx / report_ar.docx, tables.xlsx, roc.png, syntax.sps, scored_data.xlsx), 5–7 key
   findings in bullet form, and limitations/next steps.

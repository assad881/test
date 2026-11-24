---
description: كتابة قسم النتائج (Results) جاهز للمجلات المحكمة من جداول/مخرجات
argument-hint: <tables/output/summary.md path or paste>
---
Write the **Results section** for a manuscript using: $ARGUMENTS

Rules (see `assistant/knowledge/reporting_standards.md`):
- Order: participants → reliability → descriptive levels → bivariate → multivariable → (diagnostic/ROC).
- Each paragraph: lead with the finding, then numbers in parentheses, cite "(Table n)".
- Do not repeat every table cell — highlight the significant and the clinically important.
- Exact p (3 dp), `p < 0.001`, effect sizes, AOR (95% CI). Past tense. No interpretation/causation
  (that belongs in Discussion).
- Also return: suggested table titles + notes, and 3 bullet "key findings" for the abstract.
- Then run a self-check: every number in the text matches the source; flag anything unverifiable.

---
description: تفسير مخرجات SPSS/R (ملصقة أو ملف) بدقة إحصائية وصياغة جاهزة للنشر
argument-hint: <paste output or file path>
---
Interpret this statistical output for Asaad: $ARGUMENTS

Deliver in this order:
1. **What test / model this is** and whether it was the right choice (check assumptions visible in the
   output: Levene, Shapiro–Wilk, expected counts, Hosmer–Lemeshow, EPV, multicollinearity).
2. **Key numbers table**: statistic, df, p (3 dp / < 0.001), effect size (compute it if absent: d, r,
   η², Cramér's V, OR→AOR CI), and its magnitude label.
3. **Plain-language meaning** (2–3 lines, for a clinician/manager).
4. **Publication-ready paragraph** (APA, past tense, English) — no causal language for
   cross-sectional data.
5. **⚠ Red flags** and exactly what to rerun (with SPSS syntax if useful).
Never guess values that are not in the output.

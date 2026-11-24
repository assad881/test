---
description: توليد SPSS syntax جاهز للتشغيل (ترميز، إعادة ترميز، اختبارات، انحدار)
argument-hint: <what you want to do + variable names>
---
Write ready-to-run **SPSS syntax** for: $ARGUMENTS

- Use the exact variable names given; if missing, use clear placeholders in CAPS and list them.
- Include: VARIABLE LABELS / VALUE LABELS, MISSING VALUES, RECODE INTO new variables (never overwrite),
  COMPUTE scores, EXECUTE.
- Add the assumption checks needed before the main test (EXAMINE/NPPLOT, Levene, expected counts).
- Comment every block with `* ...` in English. Avoid overlapping RECODE ranges (use 59.999 style).
- After the syntax: 3-line guide on which output tables to read and what to report.

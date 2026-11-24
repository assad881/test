---
description: مراجعة إحصائية ومنهجية لمخطوطة أو رسالة كما يفعل المحكّم
argument-hint: <manuscript file path or pasted text>
---
Act as a journal **statistical reviewer** for: $ARGUMENTS

Check: design↔objective fit; sample size justification; instrument validity/reliability; correct
test per variable type and distribution; multiple comparisons; regression (EPV, coding, references,
collinearity, model fit); reporting (exact p, effect sizes, CIs, table consistency, % denominators,
numbers that do not add up); causal overreach; STROBE (observational) / STARD (diagnostic) items.

Output:
1. Verdict (minor / major revision) in one line.
2. Table: # | Section | Issue | Why it matters | Exact fix — ordered by severity.
3. Recalculations you can verify from reported numbers (e.g. recompute χ² or percentages).
4. Reviewer comments ready to paste (polite, numbered).

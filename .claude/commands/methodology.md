---
description: تصميم منهجية بحث كاملة (تصميم، عينة، أداة، تحليل) لدراسة صحية
argument-hint: <research title / objectives>
---
Design the methodology for: $ARGUMENTS

Return a structured Methods section:
1. Study design & setting (Al Dhahirah / Oman context if relevant), period.
2. Population, inclusion/exclusion criteria.
3. Sample size (use `/sample-size` logic + the engine) and sampling technique.
4. Instrument: sections, scoring, validity (expert panel/CVI), pilot & reliability (α target ≥ 0.70).
5. Variables table: variable | type | measurement | role (outcome/exposure/confounder).
6. Data collection procedure (Google Forms → Excel → SPSS) and quality control.
7. **Statistical analysis plan** mapped objective-by-objective to tests (table), α = 0.05.
8. Ethics (MoH Oman research ethics committee approval, consent, confidentiality).
9. Anticipated limitations and how they are mitigated.
Also return a filled `plan.json` draft for the automated engine.

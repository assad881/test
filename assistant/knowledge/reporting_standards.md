# AsaadStat Reporting Standards

## Numbers
| Item | Rule | Example |
|---|---|---|
| p-value | 3 dp; `< 0.001`; never `0.000` | p = 0.034 |
| Percent | 1 dp, with n | 142 (44.4%) |
| Mean/SD | 2 dp | 6.22 ± 3.01 |
| OR / AOR | 2 dp + 95% CI | AOR = 2.62 (95% CI: 1.03–6.64) |
| Correlation | rs to 2 dp | rs = 0.72, p < 0.001 |
| α / κ | 3 dp / 2 dp | α = 0.825; κ = 0.75 |

## Templates
- **t-test**: Mean X was higher among A (M ± SD) than B (M ± SD), t(df) = x.xx, p = .xxx, d = x.xx.
- **Mann–Whitney**: Median (IQR) … U = x, p = .xxx, r = x.xx.
- **ANOVA**: F(df1, df2) = x.xx, p = .xxx, η² = x.xx; post-hoc Tukey (equal var) / Games–Howell (unequal).
- **Kruskal–Wallis**: H(df) = x.xx, p = .xxx, ε² = x.xx; post-hoc Dunn with Bonferroni.
- **Chi-square**: χ²(df, N = n) = x.xx, p = .xxx, Cramér's V = x.xx.
- **Logistic**: … was associated with higher odds of Y (AOR = x.xx, 95% CI: x.xx–x.xx, p = .xxx).
  Model: χ²(df) = x.xx, p < 0.001; Nagelkerke R² = 0.xxx; Hosmer–Lemeshow p = 0.xxx; xx.x% correctly classified.
- **ROC**: AUC = 0.xx (95% CI: 0.xx–0.xx, p < 0.001); optimal cut-off (Youden) = x, Sensitivity xx.x%, Specificity xx.x%.
- **Reliability**: Cronbach's α = 0.xxx (acceptable ≥ 0.70).
- **Agreement**: κ = 0.xx (substantial, Landis & Koch), PABAK = 0.xx.

## Effect-size thresholds
- d: 0.2 small, 0.5 medium, 0.8 large · r: 0.1/0.3/0.5 · η²: 0.01/0.06/0.14 · Cramér's V (df=1): 0.1/0.3/0.5
- Spearman: <0.2 very weak, 0.2–0.39 weak, 0.4–0.59 moderate, 0.6–0.79 strong, ≥0.8 very strong
- κ (Landis & Koch): ≤0 poor, 0.01–0.20 slight, 0.21–0.40 fair, 0.41–0.60 moderate, 0.61–0.80 substantial, 0.81–1 almost perfect
- AUC: 0.5–0.6 fail, 0.6–0.7 poor, 0.7–0.8 acceptable, 0.8–0.9 excellent, >0.9 outstanding

## Language
- Cross-sectional → "associated with", never "caused / led to / effect of".
- Results = what; Discussion = why. Past tense in Results.
- Guidelines: STROBE (observational), STARD (diagnostic), CONSORT (trials), CHERRIES (online surveys).

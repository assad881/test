# Test Selection Guide

| Outcome | Exposure / groups | Normal & equal var | Otherwise |
|---|---|---|---|
| Continuous | 2 independent groups | Independent t-test | Welch t (unequal var) / Mann–Whitney U (non-normal) |
| Continuous | ≥3 independent groups | One-way ANOVA + Tukey | Welch ANOVA + Games–Howell / Kruskal–Wallis + Dunn |
| Continuous | 2 paired measures | Paired t-test | Wilcoxon signed-rank |
| Continuous | ≥3 repeated measures | Repeated-measures ANOVA | Friedman |
| Continuous | Continuous | Pearson r | Spearman rs |
| Continuous | Multiple predictors | Multiple linear regression | Transform / robust / quantile regression |
| Categorical | Categorical | Pearson χ² | Fisher's exact (2×2, >20% expected <5); merge categories (r×c) |
| Categorical (paired) | Paired | McNemar | — |
| Binary | Multiple predictors | Binary logistic regression (EPV ≥ 10) | Firth / exact logistic for sparse data |
| Ordinal | Multiple predictors | Ordinal logistic (check parallel lines) | Multinomial logistic |
| Count | Multiple predictors | Poisson | Negative binomial (overdispersion) |
| Time-to-event | Groups / predictors | Kaplan–Meier + log-rank; Cox PH | — |
| Diagnostic | Gold standard | ROC/AUC, Se, Sp, PPV, NPV, Youden cut-off | — |
| Agreement | 2 raters, categorical | Cohen's κ + PABAK | Weighted κ (ordinal); Fleiss κ (>2 raters) |
| Agreement | Continuous | ICC (two-way, absolute) + Bland–Altman | — |

**Normality**: Shapiro–Wilk (n < 50 decisive); for n ≥ 50 combine with skewness/kurtosis (|z| < 1.96 small n, |skew| < 1 large n), histogram and Q–Q plot. With n ≥ 30 per group parametric tests are usually robust (CLT).

**Regression variable selection**: include variables with p < 0.20–0.25 in bivariate analysis + clinically important confounders; check VIF < 5; state reference categories.

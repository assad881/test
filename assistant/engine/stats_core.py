"""Core statistical helpers for the AsaadStat analysis engine.

Every function returns plain dicts / DataFrames so results can be written
to Word, Excel, or Markdown without coupling to a specific output format.
"""
from __future__ import annotations

import math
import warnings

import numpy as np
import pandas as pd
from scipy import stats

warnings.filterwarnings("ignore", category=RuntimeWarning)


# ---------------------------------------------------------------- formatting
def fmt_p(p: float | None) -> str:
    if p is None or (isinstance(p, float) and math.isnan(p)):
        return "—"
    return "< 0.001" if p < 0.001 else f"{p:.3f}"


def p_text(p: float | None) -> str:
    """p-value as it appears inside a sentence: 'p < 0.001' / 'p = 0.034'."""
    s = fmt_p(p)
    return f"p {s}" if s.startswith("<") else f"p = {s}"


def mean_sd(x: pd.Series) -> str:
    x = x.dropna()
    return f"{x.mean():.2f} ± {x.std(ddof=1):.2f}" if len(x) > 1 else "—"


def median_iqr(x: pd.Series) -> str:
    x = x.dropna()
    if len(x) == 0:
        return "—"
    q1, q3 = np.percentile(x, [25, 75])
    return f"{np.median(x):.2f} ({q1:.2f}–{q3:.2f})"


# ---------------------------------------------------------------- descriptives
def frequency_table(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    rows = []
    for c in cols:
        s = df[c]
        n_valid = s.notna().sum()
        rows.append({"Variable": c, "Category": "", "n": "", "%": ""})
        for cat, n in s.value_counts(dropna=True).sort_index().items():
            rows.append({"Variable": "", "Category": str(cat), "n": int(n),
                         "%": f"{100 * n / n_valid:.1f}"})
        missing = s.isna().sum()
        if missing:
            rows.append({"Variable": "", "Category": "Missing", "n": int(missing), "%": ""})
    return pd.DataFrame(rows)


def numeric_summary(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    rows = []
    for c in cols:
        x = pd.to_numeric(df[c], errors="coerce").dropna()
        if len(x) == 0:
            continue
        sw_p = stats.shapiro(x).pvalue if 3 <= len(x) <= 5000 else np.nan
        rows.append({
            "Variable": c, "n": len(x),
            "Mean ± SD": mean_sd(x), "Median (IQR)": median_iqr(x),
            "Min–Max": f"{x.min():.2f}–{x.max():.2f}",
            "Shapiro–Wilk p": fmt_p(sw_p),
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- reliability
def cronbach_alpha(items: pd.DataFrame) -> dict:
    items = items.apply(pd.to_numeric, errors="coerce").dropna()
    k = items.shape[1]
    if k < 2 or len(items) < 3:
        return {"alpha": np.nan, "n": len(items), "k": k, "if_deleted": {}}

    def _alpha(m: pd.DataFrame) -> float:
        kk = m.shape[1]
        total_var = m.sum(axis=1).var(ddof=1)
        if total_var == 0:
            return np.nan
        return kk / (kk - 1) * (1 - m.var(ddof=1).sum() / total_var)

    if_deleted = {c: _alpha(items.drop(columns=c)) for c in items.columns} if k > 2 else {}
    return {"alpha": _alpha(items), "n": len(items), "k": k, "if_deleted": if_deleted}


def alpha_label(a: float) -> str:
    if np.isnan(a):
        return "not computable"
    for cut, lab in [(0.9, "excellent"), (0.8, "good"), (0.7, "acceptable"),
                     (0.6, "questionable"), (0.5, "poor")]:
        if a >= cut:
            return lab
    return "unacceptable"


def cohen_kappa(r1: pd.Series, r2: pd.Series) -> dict:
    """Cohen's kappa + PABAK for two raters (categorical ratings)."""
    d = pd.DataFrame({"a": r1, "b": r2}).dropna()
    cats = sorted(set(d.a) | set(d.b), key=str)
    tab = pd.crosstab(d.a, d.b).reindex(index=cats, columns=cats, fill_value=0).values
    n = tab.sum()
    po = np.trace(tab) / n
    pe = (tab.sum(0) * tab.sum(1)).sum() / n**2
    kappa = (po - pe) / (1 - pe) if pe < 1 else np.nan
    k = len(cats)
    pabak = (k * po - 1) / (k - 1) if k > 1 else np.nan
    # asymptotic SE (Fleiss) for CI
    se = math.sqrt(po * (1 - po) / (n * (1 - pe) ** 2)) if pe < 1 else np.nan
    return {"n": int(n), "observed_agreement": po, "kappa": kappa,
            "ci_low": max(-1.0, kappa - 1.96 * se), "ci_high": min(1.0, kappa + 1.96 * se), "pabak": pabak}


def kappa_label(k: float) -> str:  # Landis & Koch
    if np.isnan(k):
        return "not computable"
    for cut, lab in [(0.81, "almost perfect"), (0.61, "substantial"), (0.41, "moderate"),
                     (0.21, "fair"), (0.0, "slight")]:
        if k >= cut:
            return lab
    return "poor"


# ---------------------------------------------------------------- group comparisons
def _is_normal(groups: list[np.ndarray], alpha: float) -> bool:
    for g in groups:
        if len(g) < 3:
            return False
        if len(g) <= 5000 and stats.shapiro(g).pvalue < alpha:
            # large samples (n>=30 per group) tolerate mild non-normality (CLT)
            if len(g) < 30:
                return False
            if abs(stats.skew(g)) > 1 or abs(stats.kurtosis(g)) > 2:
                return False
    return True


def compare_groups(df: pd.DataFrame, outcome: str, by: str, alpha: float = 0.05,
                   force: str | None = None) -> dict:
    """Auto-select t-test / Welch / Mann-Whitney / ANOVA / Kruskal-Wallis."""
    d = df[[outcome, by]].copy()
    d[outcome] = pd.to_numeric(d[outcome], errors="coerce")
    d = d.dropna()
    levels = sorted(d[by].unique(), key=str)
    groups = [d.loc[d[by] == lv, outcome].values for lv in levels]
    groups_ok = [(lv, g) for lv, g in zip(levels, groups) if len(g) > 0]
    levels, groups = [x[0] for x in groups_ok], [x[1] for x in groups_ok]
    if len(groups) < 2:
        return {"error": f"'{by}' has fewer than 2 groups with data"}

    normal = _is_normal(groups, alpha) if force is None else force == "parametric"
    lev_p = stats.levene(*groups, center="median").pvalue if all(len(g) > 1 for g in groups) else np.nan
    equal_var = not (lev_p < alpha)

    if len(groups) == 2:
        if normal:
            res = stats.ttest_ind(*groups, equal_var=equal_var)
            test = "Independent t-test" if equal_var else "Welch's t-test"
            stat_lbl, stat = "t", res.statistic
            n1, n2 = len(groups[0]), len(groups[1])
            sp = math.sqrt(((n1 - 1) * groups[0].var(ddof=1) + (n2 - 1) * groups[1].var(ddof=1)) / (n1 + n2 - 2))
            effect = ("Cohen's d", (groups[0].mean() - groups[1].mean()) / sp if sp else np.nan)
        else:
            res = stats.mannwhitneyu(*groups, alternative="two-sided")
            test, stat_lbl, stat = "Mann–Whitney U", "U", res.statistic
            n1, n2 = len(groups[0]), len(groups[1])
            z = stats.norm.isf(res.pvalue / 2) if res.pvalue > 0 else np.nan
            effect = ("r", z / math.sqrt(n1 + n2) if not np.isnan(z) else np.nan)
    else:
        if normal:
            if equal_var:
                res = stats.f_oneway(*groups)
                test = "One-way ANOVA"
            else:
                res = _welch_anova(groups)
                test = "Welch's ANOVA"
            stat_lbl, stat = "F", res.statistic
            grand = np.concatenate(groups)
            ss_b = sum(len(g) * (g.mean() - grand.mean()) ** 2 for g in groups)
            ss_t = ((grand - grand.mean()) ** 2).sum()
            effect = ("η²", ss_b / ss_t if ss_t else np.nan)
        else:
            res = stats.kruskal(*groups)
            test, stat_lbl, stat = "Kruskal–Wallis H", "H", res.statistic
            n = sum(len(g) for g in groups)
            effect = ("ε²", stat / ((n**2 - 1) / (n + 1)))

    summary = mean_sd if normal else median_iqr
    return {
        "outcome": outcome, "by": by, "test": test, "parametric": normal,
        "stat_label": stat_lbl, "stat": float(stat), "p": float(res.pvalue),
        "levene_p": lev_p, "effect_label": effect[0], "effect": float(effect[1]),
        "groups": [{"level": str(lv), "n": len(g), "summary": summary(pd.Series(g)),
                    "center": float(np.mean(g) if normal else np.median(g))}
                   for lv, g in zip(levels, groups)],
    }


class _Res:
    def __init__(self, statistic, pvalue):
        self.statistic, self.pvalue = statistic, pvalue


def _welch_anova(groups):
    k = len(groups)
    n = np.array([len(g) for g in groups])
    m = np.array([g.mean() for g in groups])
    v = np.array([g.var(ddof=1) for g in groups])
    w = n / v
    mw = (w * m).sum() / w.sum()
    a = (w * (m - mw) ** 2).sum() / (k - 1)
    tmp = ((1 - w / w.sum()) ** 2 / (n - 1)).sum()
    b = 1 + 2 * (k - 2) / (k**2 - 1) * tmp
    f = a / b
    df2 = (k**2 - 1) / (3 * tmp)
    return _Res(f, stats.f.sf(f, k - 1, df2))


# ---------------------------------------------------------------- associations
def chi_square(df: pd.DataFrame, row: str, col: str) -> dict:
    d = df[[row, col]].dropna()
    tab = pd.crosstab(d[row], d[col])
    if tab.shape[0] < 2 or tab.shape[1] < 2:
        return {"error": f"{row} × {col}: need ≥2 categories in each variable"}
    chi2, p, dof, exp = stats.chi2_contingency(tab, correction=False)
    pct_low = (exp < 5).mean() * 100
    test = "Pearson χ²"
    if tab.shape == (2, 2) and pct_low > 20:
        _, p = stats.fisher_exact(tab.values)
        test = "Fisher's exact"
    n = tab.values.sum()
    cramers_v = math.sqrt(chi2 / (n * (min(tab.shape) - 1)))
    row_pct = tab.div(tab.sum(axis=1), axis=0) * 100
    return {"row": row, "col": col, "table": tab, "row_pct": row_pct, "test": test,
            "chi2": chi2, "df": dof, "p": p, "cramers_v": cramers_v,
            "pct_expected_lt5": pct_low,
            "warning": (f"{pct_low:.0f}% of cells have expected count < 5 — "
                        "consider merging categories or exact test")
            if pct_low > 20 and test != "Fisher's exact" else ""}


def spearman_matrix(df: pd.DataFrame, cols: list[str]) -> tuple[pd.DataFrame, pd.DataFrame]:
    d = df[cols].apply(pd.to_numeric, errors="coerce")
    rho = pd.DataFrame(index=cols, columns=cols, dtype=float)
    pv = rho.copy()
    for a in cols:
        for b in cols:
            if a == b:
                rho.loc[a, b], pv.loc[a, b] = 1.0, 0.0
                continue
            x = d[[a, b]].dropna()
            r, p = stats.spearmanr(x[a], x[b]) if len(x) > 2 else (np.nan, np.nan)
            rho.loc[a, b], pv.loc[a, b] = float(r), float(p)
    return rho, pv


def rho_strength(r: float) -> str:
    r = abs(r)
    return ("very strong" if r >= 0.8 else "strong" if r >= 0.6 else "moderate" if r >= 0.4
            else "weak" if r >= 0.2 else "very weak")


# ---------------------------------------------------------------- logistic regression
def logistic_regression(df: pd.DataFrame, outcome: str, predictors: list[str],
                        event=1, reference: dict | None = None) -> dict:
    import statsmodels.api as sm

    reference = reference or {}
    d = df[[outcome] + predictors].dropna().copy()
    y = (d[outcome].astype(str) == str(event)).astype(int)
    X_parts, crude = [], []
    for p in predictors:
        col = d[p]
        if pd.api.types.is_numeric_dtype(col) and col.nunique() > 5:
            part = col.astype(float).to_frame(p)
        else:
            cats = sorted(col.astype(str).unique())
            ref = str(reference.get(p, cats[0]))
            part = pd.get_dummies(col.astype(str), prefix=p, prefix_sep=": ").astype(float)
            part = part.drop(columns=f"{p}: {ref}", errors="ignore")
            part.columns = [f"{c} (ref: {ref})" for c in part.columns]
        X_parts.append(part)
        # crude (unadjusted) OR
        try:
            m0 = sm.Logit(y, sm.add_constant(part)).fit(disp=0)
            for c in part.columns:
                crude.append((c, math.exp(m0.params[c]), m0.pvalues[c]))
        except Exception:
            pass
    X = sm.add_constant(pd.concat(X_parts, axis=1))
    try:
        model = sm.Logit(y, X).fit(disp=0, maxiter=200)
    except Exception as e:  # perfect separation etc.
        return {"error": f"Model failed: {e}"}

    ci = model.conf_int()
    crude_map = {c: (o, p) for c, o, p in crude}
    rows = []
    for c in X.columns:
        if c == "const":
            continue
        co, cp = crude_map.get(c, (np.nan, np.nan))
        rows.append({"Predictor": c, "B": model.params[c], "SE": model.bse[c],
                     "Crude OR": co, "Crude p": cp,
                     "AOR": math.exp(model.params[c]),
                     "95% CI": f"{math.exp(ci.loc[c, 0]):.2f}–{math.exp(ci.loc[c, 1]):.2f}",
                     "p": model.pvalues[c]})
    n = len(y)
    ll1, ll0 = model.llf, model.llnull
    cox_snell = 1 - math.exp(2 * (ll0 - ll1) / n)
    nagelkerke = cox_snell / (1 - math.exp(2 * ll0 / n))
    pred = (model.predict(X) >= 0.5).astype(int)
    return {
        "outcome": outcome, "event": event, "n": n, "events": int(y.sum()),
        "table": pd.DataFrame(rows),
        "omnibus_chi2": 2 * (ll1 - ll0), "omnibus_df": int(model.df_model),
        "omnibus_p": float(model.llr_pvalue),
        "nagelkerke_r2": nagelkerke, "cox_snell_r2": cox_snell,
        "hosmer_lemeshow_p": _hosmer_lemeshow(y.values, model.predict(X).values),
        "accuracy": float((pred == y).mean()),
        "epv": y.sum() / max(1, X.shape[1] - 1),
    }


def _hosmer_lemeshow(y, p, g=10) -> float:
    d = pd.DataFrame({"y": y, "p": p})
    try:
        d["grp"] = pd.qcut(d.p, g, duplicates="drop")
    except ValueError:
        return np.nan
    agg = d.groupby("grp", observed=True).agg(obs=("y", "sum"), exp=("p", "sum"), n=("y", "size"))
    hl = (((agg.obs - agg.exp) ** 2) / (agg.exp * (1 - agg.exp / agg.n))).sum()
    return float(stats.chi2.sf(hl, len(agg) - 2))

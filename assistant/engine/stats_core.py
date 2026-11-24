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


# ---------------------------------------------------------------- value matching
def norm_value(v) -> str:
    """Canonical text for a data value: 1, 1.0, '1', '1.0' → '1'; strips spaces.

    Needed because a 0/1 column with any missing cell is read by pandas as float (1.0/NaN),
    so comparing str(value) with str(event) silently fails.
    """
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return ""
    if isinstance(v, (bool, np.bool_)):
        return str(int(v))
    if isinstance(v, (int, np.integer)):
        return str(int(v))
    if isinstance(v, (float, np.floating)):
        return str(int(v)) if float(v).is_integer() else repr(float(v))
    t = str(v).strip()
    try:
        f = float(t)
        if f.is_integer() and t.lstrip("+-").replace(".", "", 1).isdigit():
            return str(int(f))
    except ValueError:
        pass
    return t


def is_event(s: pd.Series, event) -> pd.Series:
    """1.0 where s equals event (type-insensitive), 0.0 otherwise, NaN where s is missing."""
    ev = norm_value(event)
    return s.map(lambda v: norm_value(v) == ev).astype(float).where(s.notna())


def _safe_exp(x) -> float:
    with np.errstate(over="ignore"):
        return float(np.exp(x))


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
def sort_categories(vc: pd.Series) -> pd.Series:
    """Sort a value_counts result by category; numbers first (numerically), then text.
    Works when a column mixes numbers and text (e.g. codes 1/2 plus 'other')."""
    def key(v):
        t = norm_value(v)
        try:
            return (0, float(t), "")
        except ValueError:
            return (1, 0.0, t)
    return vc.loc[sorted(vc.index, key=key)]


def frequency_table(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    rows = []
    for c in cols:
        s = df[c]
        n_valid = s.notna().sum()
        rows.append({"Variable": c, "Category": "", "n": "", "%": ""})
        for cat, n in sort_categories(s.value_counts(dropna=True)).items():
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
    missing_cols = [c for c in [outcome] + predictors if c not in df.columns]
    if missing_cols:
        return {"error": f"columns not found in data: {', '.join(missing_cols)}"}
    d = df[[outcome] + predictors].dropna().copy()
    y = is_event(d[outcome], event).astype(int)
    n_ev = int(y.sum())
    if n_ev == 0 or n_ev == len(y):
        found = ", ".join(sorted({norm_value(v) for v in d[outcome]}))
        return {"error": f"outcome '{outcome}' has {n_ev} events (event = '{norm_value(event)}') "
                         f"out of {len(y)}; values found: {found}"}
    X_parts, crude = [], []
    for p in predictors:
        col = d[p]
        if pd.api.types.is_numeric_dtype(col) and col.nunique() > 5:
            part = col.astype(float).to_frame(p)
        else:
            txt = col.map(norm_value)
            cats = sorted(txt.unique(), key=lambda t: (0, float(t), "") if _isnum(t) else (1, 0.0, t))
            ref = norm_value(reference.get(p, cats[0]))
            if ref not in cats:
                return {"error": f"reference '{reference.get(p)}' for '{p}' is not in the data; "
                                 f"available categories: {', '.join(cats)}"}
            part = pd.get_dummies(txt, prefix=p, prefix_sep=": ").astype(float)
            part = part.drop(columns=f"{p}: {ref}")
            part.columns = [f"{c} (ref: {ref})" for c in part.columns]
        X_parts.append(part)
        # crude (unadjusted) OR
        try:
            m0 = sm.Logit(y, sm.add_constant(part)).fit(disp=0)
            for c in part.columns:
                crude.append((c, _safe_exp(m0.params[c]), m0.pvalues[c]))
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
                     "AOR": _safe_exp(model.params[c]),
                     "95% CI": f"{_safe_exp(ci.loc[c, 0]):.2f}–{_safe_exp(ci.loc[c, 1]):.2f}",
                     "p": model.pvalues[c]})
    n = len(y)
    ll1, ll0 = model.llf, model.llnull
    cox_snell = 1 - _safe_exp(2 * (ll0 - ll1) / n)
    nagelkerke = cox_snell / (1 - _safe_exp(2 * ll0 / n))
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
        "pred": pd.Series(model.predict(X).values, index=d.index),
    }


def _isnum(t: str) -> bool:
    try:
        float(t)
        return True
    except ValueError:
        return False


def _hosmer_lemeshow(y, p, g=10) -> float:
    d = pd.DataFrame({"y": y, "p": p})
    try:
        d["grp"] = pd.qcut(d.p, g, duplicates="drop")
    except ValueError:
        return np.nan
    agg = d.groupby("grp", observed=True).agg(obs=("y", "sum"), exp=("p", "sum"), n=("y", "size"))
    hl = (((agg.obs - agg.exp) ** 2) / (agg.exp * (1 - agg.exp / agg.n))).sum()
    return float(stats.chi2.sf(hl, len(agg) - 2))


# ---------------------------------------------------------------- ROC / diagnostic accuracy
def _wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (np.nan, np.nan)
    p = k / n
    den = 1 + z**2 / n
    c = (p + z**2 / (2 * n)) / den
    h = z * math.sqrt(p * (1 - p) / n + z**2 / (4 * n**2)) / den
    return (max(0.0, c - h), min(1.0, c + h))


def _placements(pos: np.ndarray, neg: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """DeLong structural components V10 (per positive) and V01 (per negative)."""
    cmp = (pos[:, None] > neg[None, :]).astype(float) + 0.5 * (pos[:, None] == neg[None, :])
    return cmp.mean(axis=1), cmp.mean(axis=0)


def auc_label(a: float) -> str:  # Hosmer & Lemeshow
    if np.isnan(a):
        return "not computable"
    for cut, lab in [(0.9, "outstanding"), (0.8, "excellent"), (0.7, "acceptable"), (0.6, "poor")]:
        if a >= cut:
            return lab
    return "fail"


def roc_analysis(y: pd.Series, score: pd.Series, higher_is_positive: bool = True) -> dict:
    """ROC for one marker. y: 1 = event, 0 = non-event."""
    d = pd.DataFrame({"y": y, "s": pd.to_numeric(score, errors="coerce")}).dropna()
    s = d.s.values if higher_is_positive else -d.s.values
    pos, neg = s[d.y.values == 1], s[d.y.values == 0]
    n1, n0 = len(pos), len(neg)
    if n1 < 2 or n0 < 2:
        return {"error": "need ≥2 events and ≥2 non-events"}
    v10, v01 = _placements(pos, neg)
    auc = v10.mean()
    se = math.sqrt(v10.var(ddof=1) / n1 + v01.var(ddof=1) / n0)
    p = stats.mannwhitneyu(pos, neg, alternative="two-sided").pvalue   # H0: AUC = 0.5

    rows = []
    for t in np.unique(s):
        tp = int((pos >= t).sum()); fn = n1 - tp
        tn = int((neg < t).sum()); fp = n0 - tn
        rows.append({"cut": t if higher_is_positive else -t, "tp": tp, "fp": fp, "tn": tn, "fn": fn,
                     "se": tp / n1, "sp": tn / n0})
    coords = pd.DataFrame(rows)
    coords["youden"] = coords.se + coords.sp - 1
    best = coords.loc[coords.youden.idxmax()]
    tp, fp, tn, fn = int(best.tp), int(best.fp), int(best.tn), int(best.fn)
    se_, sp_ = best.se, best.sp
    return {
        "n": n1 + n0, "n_pos": n1, "n_neg": n0, "auc": auc, "se_auc": se,
        "ci": (max(0.0, auc - 1.96 * se), min(1.0, auc + 1.96 * se)), "p": p,
        "direction": "≥" if higher_is_positive else "≤", "cutoff": float(best.cut),
        "sens": se_, "sens_ci": _wilson(tp, n1), "spec": sp_, "spec_ci": _wilson(tn, n0),
        "ppv": tp / (tp + fp) if tp + fp else np.nan, "npv": tn / (tn + fn) if tn + fn else np.nan,
        "lr_pos": se_ / (1 - sp_) if sp_ < 1 else np.inf, "lr_neg": (1 - se_) / sp_ if sp_ > 0 else np.inf,
        "accuracy": (tp + tn) / (n1 + n0), "youden": float(best.youden),
        "coords": coords.sort_values("cut", ascending=higher_is_positive).reset_index(drop=True),
        "fpr_tpr": _curve(pos, neg),
    }


def _curve(pos, neg):
    thr = np.r_[np.inf, np.unique(np.r_[pos, neg])[::-1]]
    tpr = np.array([(pos >= t).mean() for t in thr])
    fpr = np.array([(neg >= t).mean() for t in thr])
    return fpr, tpr


def delong_compare(y: pd.Series, scores: dict[str, pd.Series], directions: dict[str, bool]) -> pd.DataFrame:
    """Pairwise DeLong test for correlated AUCs (complete cases across all markers)."""
    names = list(scores)
    d = pd.concat([y.rename("_y")] + [pd.to_numeric(scores[k], errors="coerce").rename(k) for k in names],
                  axis=1).dropna()
    yy = d["_y"].values
    V10, V01, aucs = [], [], []
    for k in names:
        s = d[k].values if directions.get(k, True) else -d[k].values
        a, b = _placements(s[yy == 1], s[yy == 0])
        V10.append(a); V01.append(b); aucs.append(a.mean())
    V10, V01 = np.array(V10), np.array(V01)
    S10, S01 = np.cov(V10), np.cov(V01)
    n1, n0 = V10.shape[1], V01.shape[1]
    S = S10 / n1 + S01 / n0
    rows = []
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            var = S[i, i] + S[j, j] - 2 * S[i, j]
            diff = aucs[i] - aucs[j]
            z = diff / math.sqrt(var) if var > 0 else np.nan
            rows.append({"a": names[i], "b": names[j], "diff": diff, "z": z,
                         "p": 2 * stats.norm.sf(abs(z)) if not np.isnan(z) else np.nan, "n": len(d)})
    return pd.DataFrame(rows)

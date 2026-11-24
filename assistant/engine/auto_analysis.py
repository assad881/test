"""AsaadStat Automated Research Analysis System.

Input : dataset (Excel/CSV) + analysis plan (JSON)
Output: Word report (tables + interpretation), Excel workbook of tables,
        Markdown summary, and matching SPSS syntax.

Run:
  python assistant/engine/auto_analysis.py assistant/examples/kap_plan.json
"""
from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
import stats_core as sc  # noqa: E402


# ======================================================================== data prep
def load_data(plan: dict, base: Path) -> pd.DataFrame:
    path = (base / plan["data"]).resolve()
    if path.suffix.lower() in (".xlsx", ".xls"):
        df = pd.read_excel(path, sheet_name=plan.get("sheet", 0))
    else:
        df = pd.read_csv(path)
    df.columns = [str(c).strip() for c in df.columns]
    for col, mapping in plan.get("recode", {}).items():
        df[col] = df[col].map(lambda v: mapping.get(str(v), v))
    return df


def build_scales(df: pd.DataFrame, plan: dict) -> tuple[pd.DataFrame, list[dict]]:
    """Score each scale, add <name>_score, <name>_pct, <name>_level, <name>_adequate."""
    info = []
    for name, cfg in plan.get("scales", {}).items():
        items = cfg["items"]
        block = df[items].apply(pd.to_numeric, errors="coerce")
        lo, hi = cfg.get("item_min", np.nanmin(block.values)), cfg.get("item_max", np.nanmax(block.values))
        for r in cfg.get("reverse_items", []):
            block[r] = lo + hi - block[r]
        score = block.mean(axis=1) if cfg.get("scoring", "sum") == "mean" else block.sum(axis=1, min_count=len(items))
        df[f"{name}_score"] = score
        smin = lo if cfg.get("scoring") == "mean" else lo * len(items)
        smax = hi if cfg.get("scoring") == "mean" else hi * len(items)
        pct = (score - smin) / (smax - smin) * 100
        df[f"{name}_pct"] = pct
        cuts = cfg.get("cutoffs_pct", [60, 80])          # Bloom's cut-off by default
        labels = cfg.get("labels", ["Poor", "Moderate", "Good"])
        df[f"{name}_level"] = pd.cut(pct, [-np.inf] + cuts + [np.inf], labels=labels, right=False).astype("object")
        bc = cfg.get("binary_cutoff_pct", cuts[0])
        df[f"{name}_adequate"] = pd.Series(np.where(pct >= bc, "Adequate", "Inadequate"),
                                           index=df.index, dtype="object").where(pct.notna())
        alpha = sc.cronbach_alpha(block)
        info.append({"scale": name, "items": items, "alpha": alpha, "range": (smin, smax),
                     "cuts": cuts, "labels": labels, "binary_cutoff": bc,
                     "reverse": cfg.get("reverse_items", [])})
    return df, info


# ======================================================================== report writer
class Report:
    """Collects sections and writes DOCX + XLSX + MD."""

    def __init__(self, title: str):
        self.title = title
        self.blocks: list[tuple] = []   # ("h", text) | ("p", text) | ("t", caption, df, note)
        self.n_tables = 0

    def h(self, text):
        self.blocks.append(("h", text))

    def p(self, text):
        self.blocks.append(("p", text))

    def t(self, caption, df, note=""):
        self.n_tables += 1
        self.blocks.append(("t", f"Table {self.n_tables}. {caption}", df, note))

    # ---- outputs
    def to_markdown(self, path: Path):
        out = [f"# {self.title}\n"]
        for b in self.blocks:
            if b[0] == "h":
                out.append(f"\n## {b[1]}\n")
            elif b[0] == "p":
                out.append(b[1] + "\n")
            else:
                out.append(f"**{b[1]}**\n")
                out.append(b[2].to_markdown(index=False) + "\n")
                if b[3]:
                    out.append(f"*{b[3]}*\n")
        path.write_text("\n".join(out), encoding="utf-8")

    def to_excel(self, path: Path):
        with pd.ExcelWriter(path, engine="openpyxl") as xw:
            for b in self.blocks:
                if b[0] == "t":
                    sheet = b[1].split(".")[0].replace("Table ", "T")
                    pd.DataFrame({b[1]: []}).to_excel(xw, sheet_name=sheet, index=False)
                    b[2].to_excel(xw, sheet_name=sheet, index=False, startrow=1)

    def to_docx(self, path: Path):
        from docx import Document
        from docx.enum.text import WD_ALIGN_PARAGRAPH
        from docx.oxml import OxmlElement
        from docx.oxml.ns import qn
        from docx.shared import Pt, RGBColor

        doc = Document()
        st = doc.styles["Normal"]
        st.font.name, st.font.size = "Times New Roman", Pt(11)
        doc.add_heading(self.title, 0)
        meta = doc.add_paragraph(f"Prepared by AsaadStat · {date.today():%d %B %Y}")
        meta.runs[0].font.color.rgb = RGBColor(0x55, 0x55, 0x55)

        def border(cell, **edges):
            tcPr = cell._tc.get_or_add_tcPr()
            b = OxmlElement("w:tcBorders")
            for edge, val in edges.items():
                el = OxmlElement(f"w:{edge}")
                el.set(qn("w:val"), val)
                el.set(qn("w:sz"), "8")
                b.append(el)
            tcPr.append(b)

        for blk in self.blocks:
            if blk[0] == "h":
                doc.add_heading(blk[1], 1)
            elif blk[0] == "p":
                doc.add_paragraph(blk[1]).alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            else:
                _, cap, df, note = blk
                c = doc.add_paragraph()
                c.add_run(cap).bold = True
                tbl = doc.add_table(rows=1, cols=len(df.columns))
                for i, col in enumerate(df.columns):           # APA three-line style
                    cell = tbl.rows[0].cells[i]
                    cell.text = str(col)
                    cell.paragraphs[0].runs[0].bold = True
                    border(cell, top="single", bottom="single")
                for r_i, (_, row) in enumerate(df.iterrows()):
                    cells = tbl.add_row().cells
                    for i, v in enumerate(row):
                        cells[i].text = "" if (isinstance(v, float) and np.isnan(v)) else str(v)
                        if r_i == len(df) - 1:
                            border(cells[i], bottom="single")
                for row in tbl.rows:
                    for cell in row.cells:
                        for par in cell.paragraphs:
                            for run in par.runs:
                                run.font.size = Pt(9.5)
                if note:
                    n = doc.add_paragraph()
                    r = n.add_run("Note. " + note)
                    r.italic, r.font.size = True, Pt(9)
                doc.add_paragraph()
        doc.save(path)


def r2(x, d=2):
    return "—" if x is None or (isinstance(x, float) and np.isnan(x)) else f"{x:.{d}f}"


# ======================================================================== analysis sections
def section_sample(rep: Report, df: pd.DataFrame, plan: dict):
    demo = plan.get("demographics", [])
    if not demo:
        return
    rep.h("1. Characteristics of the participants")
    ft = sc.frequency_table(df, demo)
    rep.t("Socio-demographic characteristics of the participants (N = %d)" % len(df), ft)
    sents = []
    for c in demo:
        vc = df[c].value_counts(normalize=True)
        if len(vc):
            sents.append(f"{c.replace('_', ' ')}: {vc.index[0]} ({vc.iloc[0] * 100:.1f}%)")
    rep.p(f"A total of {len(df)} participants were included in the analysis. "
          f"The most frequent categories were: " + "; ".join(sents) + " (Table %d)." % rep.n_tables)


def section_reliability(rep: Report, scales: list[dict]):
    if not scales:
        return
    rep.h("2. Reliability of the study instrument")
    rows = [{"Scale": s["scale"], "No. of items": s["alpha"]["k"], "n": s["alpha"]["n"],
             "Cronbach's α": r2(s["alpha"]["alpha"], 3),
             "Interpretation": sc.alpha_label(s["alpha"]["alpha"])} for s in scales]
    rep.t("Internal consistency of the questionnaire domains", pd.DataFrame(rows),
          "α ≥ 0.70 considered acceptable (Nunnally, 1978).")
    txt = ", ".join(f"{s['scale']} (α = {r2(s['alpha']['alpha'], 3)}, {sc.alpha_label(s['alpha']['alpha'])})"
                    for s in scales)
    rep.p(f"Internal consistency was assessed using Cronbach's alpha: {txt}.")
    weak = []
    for s in scales:
        a = s["alpha"]["alpha"]
        for item, ad in s["alpha"]["if_deleted"].items():
            if not np.isnan(ad) and ad > a + 0.02:
                weak.append(f"{item} ({s['scale']}: α if deleted = {ad:.3f})")
    if weak:
        rep.p("⚠ Items that lower reliability (review wording/coding): " + "; ".join(weak) + ".")


def section_scores(rep: Report, df: pd.DataFrame, scales: list[dict]):
    if not scales:
        return
    rep.h("3. Overall scores and levels")
    rows = []
    for s in scales:
        x = df[f"{s['scale']}_score"]
        lv = df[f"{s['scale']}_level"].value_counts()
        n = lv.sum()
        row = {"Domain": s["scale"], "Possible range": f"{s['range'][0]:g}–{s['range'][1]:g}",
               "Mean ± SD": sc.mean_sd(x), "Median (IQR)": sc.median_iqr(x)}
        for lab in s["labels"]:
            row[lab + " n (%)"] = f"{lv.get(lab, 0)} ({100 * lv.get(lab, 0) / n:.1f})" if n else "—"
        rows.append(row)
    cuts = scales[0]["cuts"]
    rep.t("Distribution of scores and levels by domain", pd.DataFrame(rows),
          f"Levels classified using percentage-score cut-offs at {', '.join(map(str, cuts))}% "
          "(modified Bloom's criteria).")
    for s in scales:
        lv = df[f"{s['scale']}_level"].value_counts(normalize=True) * 100
        parts = ", ".join(f"{lab.lower()} ({lv.get(lab, 0):.1f}%)" for lab in s["labels"])
        rep.p(f"The mean {s['scale'].lower()} score was {sc.mean_sd(df[s['scale'] + '_score'])} "
              f"out of {s['range'][1]:g}; levels were {parts}.")


def section_item_analysis(rep: Report, df: pd.DataFrame, plan: dict, scales: list[dict]):
    if not plan.get("item_tables", True) or not scales:
        return
    rep.h("4. Item-level responses")
    for s in scales:
        rows = []
        for it in s["items"]:
            vc = df[it].value_counts().sort_index()
            n = vc.sum()
            row = {"Item": plan.get("item_labels", {}).get(it, it)}
            for k, v in vc.items():
                row[str(k)] = f"{v} ({100 * v / n:.1f})"
            rows.append(row)
        rep.t(f"Item-level responses — {s['scale']} domain, n (%)", pd.DataFrame(rows).fillna("0 (0.0)"))


def section_group_comparisons(rep: Report, df: pd.DataFrame, plan: dict, alpha: float):
    cfg = plan.get("group_comparisons")
    if not cfg:
        return
    rep.h("5. Differences in scores across participant characteristics")
    for outcome in cfg["outcomes"]:
        rows, sig = [], []
        for by in cfg["by"]:
            r = sc.compare_groups(df, outcome, by, alpha, cfg.get("force"))
            if "error" in r:
                continue
            for i, g in enumerate(r["groups"]):
                rows.append({"Variable": by if i == 0 else "", "Category": g["level"], "n": g["n"],
                             ("Mean ± SD" if r["parametric"] else "Median (IQR)"): g["summary"],
                             "Test": r["test"] if i == 0 else "",
                             "Statistic": f"{r['stat_label']} = {r['stat']:.2f}" if i == 0 else "",
                             "p": sc.fmt_p(r["p"]) + ("*" if r["p"] < alpha else "") if i == 0 else "",
                             "Effect size": f"{r['effect_label']} = {r['effect']:.2f}" if i == 0 else ""})
            if r["p"] < alpha:
                hi = max(r["groups"], key=lambda g: g["center"])
                sig.append(f"{by.replace('_', ' ')} ({r['test']}, {r['stat_label']} = {r['stat']:.2f}, "
                           f"{sc.p_text(r['p'])}; highest among '{hi['level']}')")
        tdf = pd.DataFrame(rows).fillna("")
        rep.t(f"Comparison of {outcome.replace('_', ' ')} across participant characteristics", tdf,
              f"Test selected automatically from normality (Shapiro–Wilk) and homogeneity (Levene). "
              f"* Significant at p < {alpha}.")
        if sig:
            rep.p(f"{outcome.replace('_', ' ').capitalize()} differed significantly by " + "; ".join(sig) + ".")
        else:
            rep.p(f"No statistically significant differences in {outcome.replace('_', ' ')} were found "
                  f"across the examined characteristics (all p ≥ {alpha}).")


def section_associations(rep: Report, df: pd.DataFrame, plan: dict, alpha: float):
    cfg = plan.get("associations")
    if not cfg:
        return
    rep.h("6. Factors associated with the outcome levels")
    for outcome in cfg["outcomes"]:
        rows, sig, warns = [], [], []
        for by in cfg["by"]:
            r = sc.chi_square(df, by, outcome)
            if "error" in r:
                continue
            cats = list(r["table"].columns)
            for i, (lvl, cnts) in enumerate(r["table"].iterrows()):
                row = {"Variable": by if i == 0 else "", "Category": str(lvl)}
                for c in cats:
                    row[f"{c} n (%)"] = f"{cnts[c]} ({r['row_pct'].loc[lvl, c]:.1f})"
                row["χ² (df)"] = f"{r['chi2']:.2f} ({r['df']})" if i == 0 else ""
                row["p"] = (sc.fmt_p(r["p"]) + ("*" if r["p"] < alpha else "")
                            + ("ᶠ" if r["test"] == "Fisher's exact" else "")) if i == 0 else ""
                row["Cramér's V"] = f"{r['cramers_v']:.2f}" if i == 0 else ""
                rows.append(row)
            if r["p"] < alpha:
                sig.append(f"{by.replace('_', ' ')} (χ² = {r['chi2']:.2f}, {sc.p_text(r['p'])}, "
                           f"V = {r['cramers_v']:.2f})")
            if r["warning"]:
                warns.append(f"{by}: {r['warning']}")
        rep.t(f"Association between participant characteristics and {outcome.replace('_', ' ')}",
              pd.DataFrame(rows).fillna(""),
              f"Row percentages. Pearson chi-square test; ᶠ Fisher's exact test. * p < {alpha}.")
        rep.p((f"{outcome.replace('_', ' ').capitalize()} was significantly associated with "
               + "; ".join(sig) + ".") if sig else
              f"None of the characteristics were significantly associated with {outcome.replace('_', ' ')}.")
        if warns:
            rep.p("⚠ " + " | ".join(warns))


def section_correlations(rep: Report, df: pd.DataFrame, plan: dict, alpha: float):
    cols = plan.get("correlations")
    if not cols:
        return
    rep.h("7. Correlations between domains")
    rho, pv = sc.spearman_matrix(df, cols)
    tbl = pd.DataFrame(index=cols, columns=cols, dtype=object)
    sents = []
    for i, a in enumerate(cols):
        for j, b in enumerate(cols):
            if j > i:
                tbl.loc[a, b] = ""
            elif i == j:
                tbl.loc[a, b] = "1"
            else:
                star = "**" if pv.loc[a, b] < 0.01 else "*" if pv.loc[a, b] < alpha else ""
                tbl.loc[a, b] = f"{rho.loc[a, b]:.2f}{star}"
                if pv.loc[a, b] < alpha:
                    sents.append(f"{a.replace('_', ' ')} and {b.replace('_', ' ')} "
                                 f"({sc.rho_strength(rho.loc[a, b])} "
                                 f"{'positive' if rho.loc[a, b] > 0 else 'negative'}, "
                                 f"rs = {rho.loc[a, b]:.2f}, {sc.p_text(pv.loc[a, b])})")
    tbl.insert(0, "Variable", cols)
    rep.t("Spearman's rank correlation coefficients between domain scores", tbl,
          f"* p < {alpha}; ** p < 0.01.")
    rep.p(("Significant correlations were observed between " + "; ".join(sents) + ".") if sents else
          "No significant correlations were observed between the domain scores.")


def section_logistic(rep: Report, df: pd.DataFrame, plan: dict, alpha: float):
    cfg = plan.get("logistic")
    if not cfg:
        return
    rep.h("8. Predictors of the outcome (binary logistic regression)")
    r = sc.logistic_regression(df, cfg["outcome"], cfg["predictors"], cfg.get("event", 1),
                               cfg.get("reference"))
    if "error" in r:
        rep.p("⚠ " + r["error"])
        return
    t = r["table"].copy()
    out = pd.DataFrame({
        "Predictor": t["Predictor"],
        "Crude OR": t["Crude OR"].map(lambda v: r2(v)),
        "Crude p": t["Crude p"].map(sc.fmt_p),
        "B": t["B"].map(lambda v: r2(v, 3)), "SE": t["SE"].map(lambda v: r2(v, 3)),
        "AOR": t["AOR"].map(lambda v: r2(v)), "95% CI": t["95% CI"],
        "p": [sc.fmt_p(p) + ("*" if p < alpha else "") for p in t["p"]],
    })
    rep.t(f"Binary logistic regression for predictors of {cfg['outcome'].replace('_', ' ')} "
          f"(event = '{cfg.get('event', 1)}')", out,
          f"AOR, adjusted odds ratio; CI, confidence interval. Model χ²({r['omnibus_df']}) = "
          f"{r['omnibus_chi2']:.2f}, {sc.p_text(r['omnibus_p'])}; Nagelkerke R² = {r['nagelkerke_r2']:.3f}; "
          f"Hosmer–Lemeshow {sc.p_text(r['hosmer_lemeshow_p'])}; correctly classified "
          f"{r['accuracy'] * 100:.1f}%. * p < {alpha}.")
    sig = t[t["p"] < alpha]
    txt = (f"The multivariable model was statistically significant (χ²({r['omnibus_df']}) = "
           f"{r['omnibus_chi2']:.2f}, {sc.p_text(r['omnibus_p'])}; Nagelkerke R² = "
           f"{r['nagelkerke_r2']:.3f}) and correctly classified "
           f"{r['accuracy'] * 100:.1f}% of cases. ")
    if r["omnibus_p"] >= alpha:
        txt = txt.replace("was statistically significant", "was not statistically significant")
    if len(sig):
        parts = []
        for _, row in sig.iterrows():
            direction = "higher" if row["AOR"] > 1 else "lower"
            parts.append(f"{row['Predictor']} ({direction} odds; AOR = {row['AOR']:.2f}, "
                         f"95% CI: {row['95% CI']}, {sc.p_text(row['p'])})")
        txt += "Independent predictors were: " + "; ".join(parts) + "."
    else:
        txt += "No predictor remained independently significant after adjustment."
    rep.p(txt)
    checks = []
    if r["epv"] < 10:
        checks.append(f"events per variable = {r['epv']:.1f} (< 10): risk of overfitting — reduce predictors")
    if not np.isnan(r["hosmer_lemeshow_p"]) and r["hosmer_lemeshow_p"] < 0.05:
        checks.append("Hosmer–Lemeshow p < 0.05: poor calibration")
    if (t["AOR"] > 50).any() or (t["AOR"] < 0.02).any():
        checks.append("extreme ORs detected: check sparse categories / separation")
    if checks:
        rep.p("⚠ Model diagnostics: " + "; ".join(checks) + ".")


# ======================================================================== SPSS syntax
def spss_syntax(plan: dict, scales: list[dict]) -> str:
    L = ["* AsaadStat — SPSS syntax generated to mirror the automated analysis.",
         "* Open your .sav file first, then run all.", ""]
    for s in scales:
        name, items = s["scale"], s["items"]
        for rv in s["reverse"]:
            L.append(f"* Reverse-code {rv} (example for a 1–5 scale; adjust to your item range).")
            L.append(f"RECODE {rv} (1=5)(2=4)(3=3)(4=2)(5=1) INTO {rv}_r.")
        items = [f"{i}_r" if i in s["reverse"] else i for i in items]
        L += [f"RELIABILITY /VARIABLES={' '.join(items)} /SCALE('{name}') ALL",
              "  /MODEL=ALPHA /STATISTICS=DESCRIPTIVE SCALE /SUMMARY=TOTAL.",
              f"COMPUTE {name}_score = SUM.{len(items)}({', '.join(items)}).",
              f"COMPUTE {name}_pct = ({name}_score - {s['range'][0]:g}) / ({s['range'][1]:g} - {s['range'][0]:g}) * 100.",
              f"RECODE {name}_pct (LOWEST THRU {s['cuts'][0] - 0.001:g}=1) "
              + "".join(f"({c1} THRU {c2 - 0.001:g}=%d) " % (i + 2) for i, (c1, c2) in enumerate(zip(s['cuts'], s['cuts'][1:])))
              + f"({s['cuts'][-1]} THRU HIGHEST={len(s['cuts']) + 1}) INTO {name}_level.",
              f"VALUE LABELS {name}_level " + " ".join(f"{i + 1} '{l}'" for i, l in enumerate(s['labels'])) + ".",
              "EXECUTE.", ""]
    if plan.get("demographics"):
        L += [f"FREQUENCIES VARIABLES={' '.join(plan['demographics'])} /ORDER=ANALYSIS.", ""]
    if scales:
        sc_vars = " ".join(f"{s['scale']}_score" for s in scales)
        L += [f"EXAMINE VARIABLES={sc_vars} /PLOT NPPLOT /STATISTICS DESCRIPTIVES.", ""]
    gc = plan.get("group_comparisons")
    if gc:
        for by in gc["by"]:
            L += [f"* {by}: use T-TEST (2 groups) or ONEWAY (>2) if normal; else NPAR TESTS.",
                  f"NPAR TESTS /M-W= {' '.join(gc['outcomes'])} BY {by}(1 2).",
                  f"NPAR TESTS /K-W= {' '.join(gc['outcomes'])} BY {by}(1 9).", ""]
    asc = plan.get("associations")
    if asc:
        L += [f"CROSSTABS /TABLES={' '.join(asc['by'])} BY {' '.join(asc['outcomes'])}",
              "  /STATISTICS=CHISQ PHI /CELLS=COUNT ROW EXPECTED.", ""]
    if plan.get("correlations"):
        L += [f"NONPAR CORR /VARIABLES={' '.join(plan['correlations'])} /PRINT=SPEARMAN TWOTAIL NOSIG.", ""]
    lg = plan.get("logistic")
    if lg:
        L += [f"LOGISTIC REGRESSION VARIABLES {lg['outcome']}",
              f"  /METHOD=ENTER {' '.join(lg['predictors'])}",
              f"  /CONTRAST ({lg['predictors'][0]})=Indicator(1)",
              "  /PRINT=GOODFIT CI(95) /CRITERIA=PIN(.05) POUT(.10) ITERATE(20) CUT(.5).", ""]
    return "\n".join(L)


# ======================================================================== main
def run(plan_path: str):
    plan_path = Path(plan_path).resolve()
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    base = plan_path.parent
    alpha = plan.get("alpha", 0.05)
    out_dir = (base / plan.get("output_dir", "../output")).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = plan.get("project", "analysis").replace(" ", "_")

    df = load_data(plan, base)
    df, scales = build_scales(df, plan)

    rep = Report(plan.get("title", "Statistical Analysis Report"))
    rep.h("Statistical analysis (methods text)")
    rep.p(plan.get("methods_text") or (
        "Data were analysed using descriptive and inferential statistics. Categorical variables were "
        "summarised as frequencies and percentages, and continuous variables as mean ± SD or median (IQR) "
        "according to normality (Shapiro–Wilk test). Internal consistency was assessed using Cronbach's alpha. "
        "Group differences were examined using the independent t-test/one-way ANOVA or their non-parametric "
        "equivalents (Mann–Whitney U/Kruskal–Wallis), and associations between categorical variables using the "
        "chi-square or Fisher's exact test. Correlations were assessed using Spearman's rank correlation. "
        "Binary logistic regression was used to identify independent predictors, reporting adjusted odds ratios "
        f"(AOR) with 95% confidence intervals. Statistical significance was set at p < {alpha}."))
    section_sample(rep, df, plan)
    section_reliability(rep, scales)
    section_scores(rep, df, scales)
    section_item_analysis(rep, df, plan, scales)
    section_group_comparisons(rep, df, plan, alpha)
    section_associations(rep, df, plan, alpha)
    section_correlations(rep, df, plan, alpha)
    section_logistic(rep, df, plan, alpha)

    rep.to_docx(out_dir / f"{stem}_report.docx")
    rep.to_excel(out_dir / f"{stem}_tables.xlsx")
    rep.to_markdown(out_dir / f"{stem}_summary.md")
    (out_dir / f"{stem}_syntax.sps").write_text(spss_syntax(plan, scales), encoding="utf-8")
    df.to_excel(out_dir / f"{stem}_scored_data.xlsx", index=False)
    print(f"✔ {rep.n_tables} tables written to {out_dir}")
    for f in sorted(out_dir.glob(f"{stem}_*")):
        print("  -", f.name)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    run(sys.argv[1])

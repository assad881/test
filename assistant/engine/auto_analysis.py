"""AsaadStat Automated Research Analysis System.

Input : dataset (Excel/CSV) + analysis plan (JSON)
Output: Word report (tables + interpretation, English and/or Arabic RTL), Excel workbook
        of tables, Markdown summary, ROC figure, and matching SPSS syntax.

Run:
  python assistant/engine/auto_analysis.py assistant/examples/kap_plan.json
  python assistant/engine/auto_analysis.py plan.json --lang ar        # Arabic only
  python assistant/engine/auto_analysis.py plan.json --lang en,ar     # both
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
import stats_core as sc  # noqa: E402
from i18n import Lang  # noqa: E402


# ======================================================================== data prep
def load_data(plan: dict, base: Path) -> pd.DataFrame:
    path = (base / plan["data"]).resolve()
    if path.suffix.lower() in (".xlsx", ".xls"):
        df = pd.read_excel(path, sheet_name=plan.get("sheet", 0))
    else:
        df = pd.read_csv(path)
    df.columns = [str(c).strip() for c in df.columns]
    for col, mapping in plan.get("recode", {}).items():
        if col not in df.columns:
            raise KeyError(f"recode: column '{col}' not found in data")
        m = {sc.norm_value(k): v for k, v in mapping.items()}
        before = df[col]
        df[col] = before.map(lambda v: m.get(sc.norm_value(v), v) if pd.notna(v) else v)
        if before.notna().any() and not before.map(lambda v: sc.norm_value(v) in m).any():
            print(f"⚠ recode '{col}': no value matched {list(mapping)}", file=sys.stderr)
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
    """Collects sections and writes DOCX (LTR or RTL) + XLSX + MD."""

    def __init__(self, title: str, L: Lang):
        self.title, self.L = title, L
        self.blocks: list[tuple] = []  # ("h",txt) | ("p",txt) | ("t",cap,df,note,excel_only) | ("img",cap,path)
        self.n_tables = self.n_figs = 0

    def h(self, text):
        self.blocks.append(("h", text))

    def p(self, text):
        self.blocks.append(("p", text))

    def t(self, caption, df, note="", excel_only=False):
        df = df.rename(columns=self.L.head)
        if excel_only:
            self.blocks.append(("t", f"X. {caption}", df, note, True))
            return
        self.n_tables += 1
        self.blocks.append(("t", f"{self.L('table')} {self.n_tables}. {caption}", df, note, False))

    def img(self, caption, path):
        self.n_figs += 1
        self.blocks.append(("img", f"{self.L('figure')} {self.n_figs}. {caption}", path))

    # ---- outputs
    def to_markdown(self, path: Path):
        out = [f"# {self.title}\n"]
        for b in self.blocks:
            if b[0] == "h":
                out.append(f"\n## {b[1]}\n")
            elif b[0] == "p":
                out.append(b[1] + "\n")
            elif b[0] == "img":
                out.append(f"**{b[1]}**\n\n![]({Path(b[2]).name})\n")
            elif not b[4]:
                out.append(f"**{b[1]}**\n")
                out.append(b[2].to_markdown(index=False) + "\n")
                if b[3]:
                    out.append(f"*{b[3]}*\n")
        text = "\n".join(out)
        if self.L.rtl:
            text = '<div dir="rtl">\n\n' + text + "\n</div>\n"
        path.write_text(text, encoding="utf-8")

    def to_excel(self, path: Path):
        with pd.ExcelWriter(path, engine="openpyxl") as xw:
            # always write a notes sheet first so the workbook is valid even with zero tables
            notes = [b[1] for b in self.blocks if b[0] in ("h", "p")]
            pd.DataFrame({self.title: notes}).to_excel(xw, sheet_name="Notes", index=False)
            if self.L.rtl:
                xw.sheets["Notes"].sheet_view.rightToLeft = True
            k = 0
            for b in self.blocks:
                if b[0] == "t":
                    k += 1
                    sheet = f"T{k}"
                    pd.DataFrame({b[1]: []}).to_excel(xw, sheet_name=sheet, index=False)
                    b[2].to_excel(xw, sheet_name=sheet, index=False, startrow=1)
                    if self.L.rtl:
                        xw.sheets[sheet].sheet_view.rightToLeft = True

    def to_docx(self, path: Path):
        from docx import Document
        from docx.enum.text import WD_ALIGN_PARAGRAPH
        from docx.oxml import OxmlElement
        from docx.oxml.ns import qn
        from docx.shared import Inches, Pt, RGBColor

        rtl = self.L.rtl
        doc = Document()

        def set_fonts(style, size=None):
            style.font.name = "Times New Roman"
            rpr = style.element.get_or_add_rPr()
            rf = rpr.find(qn("w:rFonts"))
            if rf is None:
                rf = OxmlElement("w:rFonts")
                rpr.append(rf)
            rf.set(qn("w:cs"), "Simplified Arabic")
            if size:
                style.font.size = Pt(size)
                szcs = OxmlElement("w:szCs")
                szcs.set(qn("w:val"), str(int(size * 2 + (2 if rtl else 0))))
                rpr.append(szcs)

        set_fonts(doc.styles["Normal"], 11)
        for s in ("Title", "Heading 1"):
            set_fonts(doc.styles[s])

        def para_rtl(par):
            # In a bidi paragraph Word reads jc logically (start = right), so leave alignment
            # unset/justified; <w:bidi> must precede <w:jc> in pPr.
            if rtl:
                ppr = par._p.get_or_add_pPr()
                bidi = OxmlElement("w:bidi")
                jc = ppr.find(qn("w:jc"))
                if jc is not None:
                    jc.addprevious(bidi)
                else:
                    ppr.append(bidi)
            return par

        def border(cell, **edges):
            tcPr = cell._tc.get_or_add_tcPr()
            b = OxmlElement("w:tcBorders")
            for edge, val in edges.items():
                el = OxmlElement(f"w:{edge}")
                el.set(qn("w:val"), val)
                el.set(qn("w:sz"), "8")
                b.append(el)
            tcPr.append(b)

        from docx.enum.section import WD_ORIENT, WD_SECTION

        def sect_rtl(sec):
            if rtl and sec._sectPr.find(qn("w:bidi")) is None:
                sec._sectPr.append(OxmlElement("w:bidi"))

        state = {"landscape": False}

        def orient(landscape: bool):
            """Wide tables (≥ 8 columns) go on landscape pages."""
            if landscape == state["landscape"]:
                return
            sec = doc.add_section(WD_SECTION.NEW_PAGE)
            w, h = sec.page_width, sec.page_height
            if (landscape and w < h) or (not landscape and w > h):
                sec.page_width, sec.page_height = h, w
            sec.orientation = WD_ORIENT.LANDSCAPE if landscape else WD_ORIENT.PORTRAIT
            sect_rtl(sec)
            state["landscape"] = landscape

        sect_rtl(doc.sections[0])
        para_rtl(doc.add_heading(self.title, 0))
        meta = para_rtl(doc.add_paragraph(self.L("prepared_by", d=f"{date.today():%d/%m/%Y}")))
        meta.runs[0].font.color.rgb = RGBColor(0x55, 0x55, 0x55)

        for blk in self.blocks:
            if blk[0] != "t":
                orient(False)
            if blk[0] == "h":
                para_rtl(doc.add_heading(blk[1], 1))
            elif blk[0] == "p":
                par = doc.add_paragraph(blk[1])
                par.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
                para_rtl(par)
            elif blk[0] == "img":
                c = para_rtl(doc.add_paragraph())
                c.add_run(blk[1]).bold = True
                doc.add_picture(str(blk[2]), width=Inches(5.2))
                doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
                doc.add_paragraph()
            else:
                _, cap, df, note, excel_only = blk
                if excel_only:
                    continue
                orient(len(df.columns) >= 8)
                c = para_rtl(doc.add_paragraph())
                c.add_run(cap).bold = True
                tbl = doc.add_table(rows=1, cols=len(df.columns))
                if rtl:
                    tbl._tbl.tblPr.append(OxmlElement("w:bidiVisual"))
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
                            # numeric/Latin-only cells stay LTR so brackets and minus signs are not mirrored
                            if ARABIC.search(par.text):
                                para_rtl(par)
                            for run in par.runs:
                                run.font.size = Pt(9.5)
                if note:
                    n = para_rtl(doc.add_paragraph())
                    r = n.add_run(self.L("note") + " " + note)
                    r.italic, r.font.size = True, Pt(9)
                doc.add_paragraph()
        doc.save(path)


ARABIC = re.compile(r"[\u0600-\u06FF]")


def r2(x, d=2):
    return "—" if x is None or (isinstance(x, float) and (np.isnan(x) or np.isinf(x))) else f"{x:.{d}f}"


# ======================================================================== analysis sections
def section_sample(rep: Report, df: pd.DataFrame, plan: dict, L: Lang):
    demo = plan.get("demographics", [])
    if not demo:
        return
    rep.h(L("h_sample"))
    ft = sc.frequency_table(df, demo)
    ft["Variable"] = ft["Variable"].map(lambda v: L.v(v) if v else v)
    ft["Category"] = ft["Category"].map(lambda c: L("missing") if c == "Missing" else L.val(c) if c else c)
    rep.t(L("cap_sample", n=len(df)), ft)
    sents = []
    for c in demo:
        vc = df[c].value_counts(normalize=True)
        if len(vc):
            sents.append(f"{L.v(c)}: {L.val(vc.index[0])} ({vc.iloc[0] * 100:.1f}%)")
    rep.p(L("p_sample", n=len(df), items=L.comma().join(sents), t=rep.n_tables))


def section_reliability(rep: Report, scales: list[dict], L: Lang):
    if not scales:
        return
    rep.h(L("h_rel"))
    rows = [{"Scale": L.v(s["scale"]), "No. of items": s["alpha"]["k"], "n": s["alpha"]["n"],
             "Cronbach's α": r2(s["alpha"]["alpha"], 3),
             "Interpretation": L.w(sc.alpha_label(s["alpha"]["alpha"]))} for s in scales]
    rep.t(L("cap_rel"), pd.DataFrame(rows), L("note_rel"))
    sep = "، " if L.rtl else ", "
    txt = sep.join(f"{L.v(s['scale'])} (α = {r2(s['alpha']['alpha'], 3)}) {L.w(sc.alpha_label(s['alpha']['alpha']))}"
                   if L.rtl else
                   f"{L.v(s['scale'])} (α = {r2(s['alpha']['alpha'], 3)}, {sc.alpha_label(s['alpha']['alpha'])})"
                   for s in scales)
    rep.p(L("p_rel", items=txt))
    weak = []
    for s in scales:
        a = s["alpha"]["alpha"]
        for item, ad in s["alpha"]["if_deleted"].items():
            if not np.isnan(ad) and ad > a + 0.02:
                weak.append(f"{item} ({L.v(s['scale'])}: {L('if_deleted')} = {ad:.3f})")
    if weak:
        rep.p(L("p_rel_weak", items=L.comma().join(weak)))


def section_scores(rep: Report, df: pd.DataFrame, scales: list[dict], L: Lang):
    if not scales:
        return
    rep.h(L("h_scores"))
    rows = []
    for s in scales:
        x = df[f"{s['scale']}_score"]
        lv = df[f"{s['scale']}_level"].value_counts()
        n = lv.sum()
        row = {"Domain": L.v(s["scale"]), "Possible range": f"{s['range'][0]:g}–{s['range'][1]:g}",
               "Mean ± SD": sc.mean_sd(x), "Median (IQR)": sc.median_iqr(x)}
        for lab in s["labels"]:
            row[L.val(lab) + " n (%)"] = f"{lv.get(lab, 0)} ({100 * lv.get(lab, 0) / n:.1f})" if n else "—"
        rows.append(row)
    rep.t(L("cap_scores"), pd.DataFrame(rows), L("note_scores", cuts=", ".join(map(str, scales[0]["cuts"]))))
    sep = "، " if L.rtl else ", "
    for s in scales:
        lv = df[f"{s['scale']}_level"].value_counts(normalize=True) * 100
        parts = sep.join(f"{L.val(lab) if L.rtl else lab.lower()} ({lv.get(lab, 0):.1f}%)" for lab in s["labels"])
        rep.p(L("p_score", scale=L.v(s["scale"]) if L.rtl else L.v(s["scale"]).lower(),
                msd=sc.mean_sd(df[s["scale"] + "_score"]), mx=f"{s['range'][1]:g}", parts=parts))


def section_item_analysis(rep: Report, df: pd.DataFrame, plan: dict, scales: list[dict], L: Lang):
    if not plan.get("item_tables", True) or not scales:
        return
    rep.h(L("h_items"))
    for s in scales:
        rows = []
        for it in s["items"]:
            vc = sc.sort_categories(df[it].value_counts())
            n = vc.sum()
            row = {"Item": L.v(it) if it in L.var_labels else plan.get("item_labels", {}).get(it, it)}
            for k, v in vc.items():
                row[str(k)] = f"{v} ({100 * v / n:.1f})"
            rows.append(row)
        rep.t(L("cap_items", scale=L.v(s["scale"])), pd.DataFrame(rows).fillna("0 (0.0)"))


def section_group_comparisons(rep: Report, df: pd.DataFrame, plan: dict, alpha: float, L: Lang):
    cfg = plan.get("group_comparisons")
    if not cfg:
        return
    rep.h(L("h_groups"))
    for outcome in cfg["outcomes"]:
        rows, sig = [], []
        for by in cfg["by"]:
            r = sc.compare_groups(df, outcome, by, alpha, cfg.get("force"))
            if "error" in r:
                continue
            for i, g in enumerate(r["groups"]):
                rows.append({"Variable": L.v(by) if i == 0 else "", "Category": L.val(g["level"]), "n": g["n"],
                             ("Mean ± SD" if r["parametric"] else "Median (IQR)"): g["summary"],
                             "Test": L.w(r["test"]) if i == 0 else "",
                             "Statistic": f"{r['stat_label']} = {r['stat']:.2f}" if i == 0 else "",
                             "p": sc.fmt_p(r["p"]) + ("*" if r["p"] < alpha else "") if i == 0 else "",
                             "Effect size": f"{r['effect_label']} = {r['effect']:.2f}" if i == 0 else ""})
            if r["p"] < alpha:
                hi = max(r["groups"], key=lambda g: g["center"])
                sig.append(L("p_groups_item", by=L.v(by), test=L.w(r["test"]),
                             stat=f"{r['stat_label']} = {r['stat']:.2f}", p=sc.p_text(r["p"]), hi=L.val(hi["level"])))
        rep.t(L("cap_groups", o=L.v(outcome)), pd.DataFrame(rows).fillna(""), L("note_groups", a=alpha))
        o = L.v(outcome)
        rep.p(L("p_groups_sig", o=o if L.rtl else o[:1].upper() + o[1:], items=L.comma().join(sig))
              if sig else L("p_groups_ns", o=o, a=alpha))


def section_associations(rep: Report, df: pd.DataFrame, plan: dict, alpha: float, L: Lang):
    cfg = plan.get("associations")
    if not cfg:
        return
    rep.h(L("h_assoc"))
    for outcome in cfg["outcomes"]:
        rows, sig, warns = [], [], []
        for by in cfg["by"]:
            r = sc.chi_square(df, by, outcome)
            if "error" in r:
                continue
            cats = list(r["table"].columns)
            for i, (lvl, cnts) in enumerate(r["table"].iterrows()):
                row = {"Variable": L.v(by) if i == 0 else "", "Category": L.val(lvl)}
                for c in cats:
                    row[f"{L.val(c)} n (%)"] = f"{cnts[c]} ({r['row_pct'].loc[lvl, c]:.1f})"
                row["χ² (df)"] = f"{r['chi2']:.2f} ({r['df']})" if i == 0 else ""
                row["p"] = (sc.fmt_p(r["p"]) + ("*" if r["p"] < alpha else "")
                            + ("ᶠ" if r["test"] == "Fisher's exact" else "")) if i == 0 else ""
                row["Cramér's V"] = f"{r['cramers_v']:.2f}" if i == 0 else ""
                rows.append(row)
            if r["p"] < alpha:
                sig.append(f"{L.v(by)} (χ² = {r['chi2']:.2f}, {sc.p_text(r['p'])}, V = {r['cramers_v']:.2f})")
            if r["warning"]:
                warns.append(f"{L.v(by)}: " + L("cells_warn", pct=f"{r['pct_expected_lt5']:.0f}"))
        o = L.v(outcome)
        rep.t(L("cap_assoc", o=o), pd.DataFrame(rows).fillna(""), L("note_assoc", a=alpha))
        rep.p(L("p_assoc_sig", o=o if L.rtl else o[:1].upper() + o[1:], items=L.comma().join(sig))
              if sig else L("p_assoc_ns", o=o))
        if warns:
            rep.p("⚠ " + " | ".join(warns))


def section_correlations(rep: Report, df: pd.DataFrame, plan: dict, alpha: float, L: Lang):
    cols = plan.get("correlations")
    if not cols:
        return
    rep.h(L("h_corr"))
    rho, pv = sc.spearman_matrix(df, cols)
    names = [L.v(c) for c in cols]
    tbl = pd.DataFrame(index=cols, columns=names, dtype=object)
    sents = []
    for i, a in enumerate(cols):
        for j, b in enumerate(cols):
            if j > i:
                tbl.loc[a, names[j]] = ""
            elif i == j:
                tbl.loc[a, names[j]] = "1"
            else:
                star = "**" if pv.loc[a, b] < 0.01 else "*" if pv.loc[a, b] < alpha else ""
                tbl.loc[a, names[j]] = f"{rho.loc[a, b]:.2f}{star}"
                if pv.loc[a, b] < alpha:
                    sents.append(L("p_corr_item", a=L.v(a), b=L.v(b), strength=L.w(sc.rho_strength(rho.loc[a, b])),
                                   dir=L("positive") if rho.loc[a, b] > 0 else L("negative"),
                                   r=f"{rho.loc[a, b]:.2f}", p=sc.p_text(pv.loc[a, b])))
    tbl.insert(0, "Variable", names)
    rep.t(L("cap_corr"), tbl, L("note_corr", a=alpha))
    rep.p(L("p_corr_sig", items=L.comma().join(sents)) if sents else L("p_corr_ns"))


def section_logistic(rep: Report, df: pd.DataFrame, plan: dict, alpha: float, L: Lang) -> dict | None:
    cfg = plan.get("logistic")
    if not cfg:
        return None
    rep.h(L("h_logit"))
    r = sc.logistic_regression(df, cfg["outcome"], cfg["predictors"], cfg.get("event", 1), cfg.get("reference"))
    if "error" in r:
        rep.p(L("model_failed", e=r["error"]))
        return None
    t = r["table"].copy()
    pred_names = t["Predictor"].map(lambda s: _pred_label(s, L))
    out = pd.DataFrame({
        "Predictor": pred_names,
        "Crude OR": t["Crude OR"].map(lambda v: r2(v)),
        "Crude p": t["Crude p"].map(sc.fmt_p),
        "B": t["B"].map(lambda v: r2(v, 3)), "SE": t["SE"].map(lambda v: r2(v, 3)),
        "AOR": t["AOR"].map(lambda v: r2(v)), "95% CI": t["95% CI"],
        "p": [sc.fmt_p(p) + ("*" if p < alpha else "") for p in t["p"]],
    })
    ev = L.val(cfg.get("event", 1))
    kw = dict(df=r["omnibus_df"], chi=f"{r['omnibus_chi2']:.2f}", p=sc.p_text(r["omnibus_p"]),
              r2=f"{r['nagelkerke_r2']:.3f}", acc=f"{r['accuracy'] * 100:.1f}")
    rep.t(L("cap_logit", o=L.v(cfg["outcome"]), e=ev), out,
          L("note_logit", hl=sc.p_text(r["hosmer_lemeshow_p"]), a=alpha, **kw))
    txt = L("p_logit_model_sig" if r["omnibus_p"] < alpha else "p_logit_model_ns", **kw)
    sig = t[t["p"] < alpha]
    if len(sig):
        parts = [L("p_logit_item", v=_pred_label(row["Predictor"], L),
                   dir=L("higher") if row["AOR"] > 1 else L("lower"), aor=f"{row['AOR']:.2f}",
                   ci=row["95% CI"], p=sc.p_text(row["p"])) for _, row in sig.iterrows()]
        txt += L("p_logit_pred", items=L.comma().join(parts))
    else:
        txt += L("p_logit_none")
    rep.p(txt)
    checks = []
    if r["epv"] < 10:
        checks.append(L("diag_epv", epv=f"{r['epv']:.1f}"))
    if not np.isnan(r["hosmer_lemeshow_p"]) and r["hosmer_lemeshow_p"] < 0.05:
        checks.append(L("diag_hl"))
    if (t["AOR"] > 50).any() or (t["AOR"] < 0.02).any():
        checks.append(L("diag_or"))
    if checks:
        rep.p(L("diag", items=L.comma().join(checks)))
    return r


def _pred_label(raw: str, L: Lang) -> str:
    """'gender: Male (ref: Female)' → localized variable name + localized 'ref'."""
    m = re.match(r"^(.*?): (.*) \(ref: (.*)\)$", raw)
    if m:
        var, val, ref = m.groups()
        return f"{L.v(var)}: {L.val(val)} ({L('ref')}: {L.val(ref)})"
    return L.v(raw)


def section_roc(rep: Report, df: pd.DataFrame, plan: dict, alpha: float, L: Lang, out_dir: Path,
                stem: str, logit: dict | None):
    cfg = plan.get("roc")
    if not cfg:
        return
    rep.h(L("h_roc"))
    event = cfg.get("event", 1)
    y = sc.is_event(df[cfg["outcome"]], event)
    directions = {m: cfg.get("direction", {}).get(m, "higher") != "lower" for m in cfg["markers"]}
    scores = {m: df[m] for m in cfg["markers"]}
    if cfg.get("include_logistic_model") and logit is not None:
        key = L("logit_model")
        scores[key] = logit["pred"].reindex(df.index)
        directions[key] = True
    rows, rows_cut, results, notes = [], [], {}, []
    for m, s in scores.items():
        r = sc.roc_analysis(y, s, directions[m])
        if "error" in r:
            notes.append(f"⚠ {L.v(m)}: {r['error']}")
            continue
        results[m] = r
        is_prob = m == L("logit_model")
        cut = f"{r['direction']} {r['cutoff']:.2f}" if is_prob or r["cutoff"] % 1 else f"{r['direction']} {r['cutoff']:g}"
        rows.append({
            "Marker": L.v(m), "n": r["n"],
            "AUC (95% CI)": f"{r['auc']:.3f} ({r['ci'][0]:.3f}–{r['ci'][1]:.3f})",
            "p": sc.fmt_p(r["p"]) + ("*" if r["p"] < alpha else ""),
            "Discrimination": L.auc(sc.auc_label(r["auc"])),
        })
        rows_cut.append({
            "Marker": L.v(m), "Cut-off": cut,
            "Se % (95% CI)": f"{r['sens'] * 100:.1f} ({r['sens_ci'][0] * 100:.1f}–{r['sens_ci'][1] * 100:.1f})",
            "Sp % (95% CI)": f"{r['spec'] * 100:.1f} ({r['spec_ci'][0] * 100:.1f}–{r['spec_ci'][1] * 100:.1f})",
            "PPV %": r2(r["ppv"] * 100, 1), "NPV %": r2(r["npv"] * 100, 1),
            "LR+": r2(r["lr_pos"]), "LR−": r2(r["lr_neg"]), "Youden J": f"{r['youden']:.3f}",
        })
        if r["auc"] < 0.5:
            notes.append(L("roc_inverse", m=m))
        r["cut_txt"] = cut
    if not results:
        for n in notes:
            rep.p(n)
        return
    prev = y.mean() * 100
    rep.t(L("cap_roc", o=L.v(cfg["outcome"]), e=L.val(event)), pd.DataFrame(rows), L("note_roc_auc"))
    rep.t(L("cap_roc_cut", o=L.v(cfg["outcome"])), pd.DataFrame(rows_cut), L("note_roc", prev=f"{prev:.1f}"))
    for m, r in results.items():
        rep.p(L("p_roc_item", m=L.v(m), lab=L.auc(sc.auc_label(r["auc"])), auc=f"{r['auc']:.3f}",
                ci=f"{r['ci'][0]:.3f}–{r['ci'][1]:.3f}", p=sc.p_text(r["p"]), cut=r["cut_txt"],
                se=f"{r['sens'] * 100:.1f}", sp=f"{r['spec'] * 100:.1f}", j=f"{r['youden']:.3f}"))
    for n in notes:
        rep.p(n)

    if len(results) >= 2:
        cmp = sc.delong_compare(y, {m: scores[m] for m in results}, directions)
        rep.t(L("cap_roc_cmp"), pd.DataFrame({
            "Comparison": [f"{L.v(a)} vs {L.v(b)}" for a, b in zip(cmp.a, cmp.b)],
            "ΔAUC": cmp["diff"].map(lambda v: f"{v:.3f}"), "z": cmp.z.map(lambda v: r2(v)),
            "p": [sc.fmt_p(p) + ("*" if p < alpha else "") for p in cmp.p], "n": cmp.n}))
        sig = cmp[cmp.p < alpha]
        if len(sig):
            for _, c in sig.iterrows():
                rep.p(L("p_roc_cmp", a=L.v(c.a), b=L.v(c.b), d=f"{c['diff']:.3f}", p=sc.p_text(c.p)))
        else:
            rep.p(L("p_roc_cmp_ns"))

    # figure (legend in Latin script — matplotlib cannot shape Arabic without extra libs)
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    en = Lang("en", L.var_labels)
    fig, ax = plt.subplots(figsize=(5.2, 5), dpi=200)
    for m, r in results.items():
        fpr, tpr = r["fpr_tpr"]
        name = "Logistic model" if m == L("logit_model") else en.v(m)
        ax.step(fpr, tpr, where="post", lw=1.8, label=f"{name} (AUC = {r['auc']:.3f})")
        ax.plot(1 - r["spec"], r["sens"], "o", ms=5, color=ax.lines[-1].get_color())
    ax.plot([0, 1], [0, 1], "--", color="grey", lw=1)
    ax.set_xlabel("1 − Specificity")
    ax.set_ylabel("Sensitivity")
    ax.set_xlim(0, 1); ax.set_ylim(0, 1.01)
    ax.legend(loc="lower right", fontsize=8, frameon=False)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig_path = out_dir / f"{stem}_roc.png"
    fig.savefig(fig_path)
    plt.close(fig)
    rep.img(L("cap_roc_fig", o=L.v(cfg["outcome"])), fig_path)

    for m, r in results.items():   # full coordinate tables → Excel only
        c = r["coords"]
        rep.t(L("cap_roc_coords", m=L.v(m)), pd.DataFrame({
            "Cut-off": [f"{r['direction']} {v:.3f}".rstrip("0").rstrip(".") for v in c.cut],
            "Sensitivity": (c.se * 100).round(1), "Specificity": (c.sp * 100).round(1),
            "1 − Specificity": ((1 - c.sp) * 100).round(1), "Youden J": c.youden.round(3)}), excel_only=True)


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
              f"RECODE {name}_pct (LOWEST THRU {s['binary_cutoff'] - 0.001:g}=0) (ELSE=1) INTO {name}_adequate.",
              f"VALUE LABELS {name}_adequate 0 'Inadequate' 1 'Adequate'.",
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
              "  /SAVE=PRED(PRE_1)",
              "  /PRINT=GOODFIT CI(95) /CRITERIA=PIN(.05) POUT(.10) ITERATE(20) CUT(.5).", ""]
    roc = plan.get("roc")
    if roc:
        markers = list(roc["markers"]) + (["PRE_1"] if roc.get("include_logistic_model") and lg else [])
        large = all(roc.get("direction", {}).get(m, "higher") != "lower" for m in roc["markers"])
        L += ["* ROC: the state variable must be numeric (1 = event). Recode first if it is text.",
              f"ROC {' '.join(markers)} BY {roc['outcome']} (1)",
              "  /PLOT=CURVE(REFERENCE)",
              "  /PRINT=SE COORDINATES",
              f"  /CRITERIA=CUTOFF(INCLUDE) TESTPOS({'LARGE' if large else 'SMALL'}) DISTRIBUTION(FREE) CI(95)",
              "  /MISSING=EXCLUDE.",
              "* Youden J = Sensitivity + Specificity - 1 (compute from the coordinates table).", ""]
    return "\n".join(L)


# ======================================================================== main
def run(plan_path: str, langs: list[str] | None = None):
    plan_path = Path(plan_path).resolve()
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    base = plan_path.parent
    alpha = plan.get("alpha", 0.05)
    out_dir = (base / plan.get("output_dir", "../output")).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = plan.get("project", "analysis").replace(" ", "_")
    langs = langs or plan.get("languages") or [plan.get("language", "en")]

    df = load_data(plan, base)
    df, scales = build_scales(df, plan)

    for code in langs:
        L = Lang(code, plan.get("var_labels"), plan.get("value_labels_ar"))
        title = plan.get(f"title_{code}") or plan.get("title") or L("default_title")
        suffix = "" if code == "en" else f"_{code}"
        rep = Report(title, L)
        rep.h(L("h_methods"))
        custom = plan.get(f"methods_text_{code}") or (plan.get("methods_text") if code == "en" else None)
        rep.p(custom or L("methods", a=alpha, roc=L("methods_roc") if plan.get("roc") else ""))
        section_sample(rep, df, plan, L)
        section_reliability(rep, scales, L)
        section_scores(rep, df, scales, L)
        section_item_analysis(rep, df, plan, scales, L)
        section_group_comparisons(rep, df, plan, alpha, L)
        section_associations(rep, df, plan, alpha, L)
        section_correlations(rep, df, plan, alpha, L)
        logit = section_logistic(rep, df, plan, alpha, L)
        section_roc(rep, df, plan, alpha, L, out_dir, stem, logit)

        rep.to_docx(out_dir / f"{stem}_report{suffix}.docx")
        rep.to_excel(out_dir / f"{stem}_tables{suffix}.xlsx")
        rep.to_markdown(out_dir / f"{stem}_summary{suffix}.md")
        print(f"✔ [{code}] {rep.n_tables} tables, {rep.n_figs} figure(s)")

    (out_dir / f"{stem}_syntax.sps").write_text(spss_syntax(plan, scales), encoding="utf-8")
    df.to_excel(out_dir / f"{stem}_scored_data.xlsx", index=False)
    print(f"Output folder: {out_dir}")
    for f in sorted(out_dir.glob(f"{stem}_*")):
        print("  -", f.name)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("plan")
    ap.add_argument("--lang", help="en, ar, or en,ar (overrides plan 'languages')")
    a = ap.parse_args()
    run(a.plan, a.lang.split(",") if a.lang else None)

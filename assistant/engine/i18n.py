"""Bilingual (English / Arabic) text for AsaadStat reports.

Statistical symbols, test names and numbers stay in Latin script in both languages
(standard practice in Gulf academic and MoH reports).
"""
from __future__ import annotations

S = {
    # ------------------------------------------------------------------ general
    "prepared_by": {"en": "Prepared by AsaadStat · {d}", "ar": "إعداد: AsaadStat · {d}"},
    "table": {"en": "Table", "ar": "جدول"},
    "figure": {"en": "Figure", "ar": "شكل"},
    "note": {"en": "Note.", "ar": "ملاحظة:"},
    "default_title": {"en": "Statistical Analysis Report", "ar": "تقرير التحليل الإحصائي"},
    "sig_note": {"en": "* Significant at p < {a}.", "ar": "* دالّ إحصائياً عند p < {a}."},

    # ------------------------------------------------------------------ methods
    "h_methods": {"en": "Statistical analysis (methods text)", "ar": "التحليل الإحصائي (نص المنهجية)"},
    "methods": {
        "en": ("Data were analysed using descriptive and inferential statistics. Categorical variables were "
               "summarised as frequencies and percentages, and continuous variables as mean ± SD or median (IQR) "
               "according to normality (Shapiro–Wilk test). Internal consistency was assessed using Cronbach's alpha. "
               "Group differences were examined using the independent t-test/one-way ANOVA or their non-parametric "
               "equivalents (Mann–Whitney U/Kruskal–Wallis), and associations between categorical variables using the "
               "chi-square or Fisher's exact test. Correlations were assessed using Spearman's rank correlation. "
               "Binary logistic regression was used to identify independent predictors, reporting adjusted odds "
               "ratios (AOR) with 95% confidence intervals. {roc}Statistical significance was set at p < {a}."),
        "ar": ("حُلِّلت البيانات باستخدام الإحصاء الوصفي والاستدلالي. لُخِّصت المتغيرات الفئوية بالتكرارات والنسب "
               "المئوية، والمتغيرات الكمية بالمتوسط ± الانحراف المعياري أو الوسيط (المدى الربيعي) بحسب اعتدالية "
               "التوزيع (اختبار Shapiro–Wilk). وقيس الاتساق الداخلي للأداة بمعامل ألفا كرونباخ (Cronbach's α). "
               "وفُحصت الفروق بين المجموعات باختبار t للعينات المستقلة أو تحليل التباين الأحادي (ANOVA) أو بدائلهما "
               "اللامعلمية (Mann–Whitney U / Kruskal–Wallis)، والعلاقة بين المتغيرات الفئوية باختبار مربع كاي (χ²) "
               "أو اختبار فيشر الدقيق. وقيس الارتباط بمعامل سبيرمان (Spearman). واستُخدم الانحدار اللوجستي الثنائي "
               "لتحديد العوامل المنبئة المستقلة، مع عرض نسب الأرجحية المعدّلة (AOR) وفترات ثقة 95%. {roc}"
               "وعُدَّت النتائج ذات دلالة إحصائية عند p < {a}."),
    },
    "methods_roc": {
        "en": ("Discriminative ability was assessed using receiver operating characteristic (ROC) curve analysis "
               "and the area under the curve (AUC), and the optimal cut-off was identified using the Youden index. "),
        "ar": ("وقُيِّمت القدرة التمييزية باستخدام تحليل منحنى خصائص التشغيل (ROC) والمساحة تحت المنحنى (AUC)، "
               "وحُدِّدت نقطة القطع المثلى بمؤشر Youden. "),
    },

    # ------------------------------------------------------------------ sample
    "h_sample": {"en": "1. Characteristics of the participants", "ar": "1. خصائص المشاركين"},
    "cap_sample": {"en": "Socio-demographic characteristics of the participants (N = {n})",
                   "ar": "الخصائص الديموغرافية والاجتماعية للمشاركين (N = {n})"},
    "p_sample": {"en": "A total of {n} participants were included in the analysis. The most frequent categories were: {items} (Table {t}).",
                 "ar": "شملت الدراسة {n} مشاركاً. وكانت الفئات الأكثر تكراراً: {items} (جدول {t})."},
    "missing": {"en": "Missing", "ar": "بيانات مفقودة"},

    # ------------------------------------------------------------------ reliability
    "h_rel": {"en": "2. Reliability of the study instrument", "ar": "2. ثبات أداة الدراسة"},
    "cap_rel": {"en": "Internal consistency of the questionnaire domains", "ar": "الاتساق الداخلي لمحاور الاستبانة"},
    "note_rel": {"en": "α ≥ 0.70 considered acceptable (Nunnally, 1978).",
                 "ar": "تُعدّ قيمة α ≥ 0.70 مقبولة (Nunnally, 1978)."},
    "p_rel": {"en": "Internal consistency was assessed using Cronbach's alpha: {items}.",
              "ar": "قيس الاتساق الداخلي بمعامل ألفا كرونباخ، وجاءت النتائج كالآتي: {items}."},
    "p_rel_weak": {"en": "⚠ Items that lower reliability (review wording/coding): {items}.",
                   "ar": "⚠ بنود تُخفِّض الثبات (راجع الصياغة/الترميز): {items}."},
    "if_deleted": {"en": "α if deleted", "ar": "α عند الحذف"},

    # ------------------------------------------------------------------ scores
    "h_scores": {"en": "3. Overall scores and levels", "ar": "3. الدرجات الكلية والمستويات"},
    "cap_scores": {"en": "Distribution of scores and levels by domain", "ar": "توزيع الدرجات والمستويات حسب المحور"},
    "note_scores": {"en": "Levels classified using percentage-score cut-offs at {cuts}% (modified Bloom's criteria).",
                    "ar": "صُنِّفت المستويات وفق نقاط قطع للنسبة المئوية للدرجة عند {cuts}% (معيار Bloom المعدّل)."},
    "p_score": {"en": "The mean {scale} score was {msd} out of {mx}; levels were {parts}.",
                "ar": "بلغ متوسط درجة {scale} {msd} من أصل {mx}، وتوزعت المستويات كالآتي: {parts}."},

    # ------------------------------------------------------------------ items
    "h_items": {"en": "4. Item-level responses", "ar": "4. الاستجابات على مستوى البنود"},
    "cap_items": {"en": "Item-level responses — {scale} domain, n (%)", "ar": "الاستجابات على بنود محور {scale}، n (%)"},

    # ------------------------------------------------------------------ group comparisons
    "h_groups": {"en": "5. Differences in scores across participant characteristics",
                 "ar": "5. الفروق في الدرجات حسب خصائص المشاركين"},
    "cap_groups": {"en": "Comparison of {o} across participant characteristics",
                   "ar": "مقارنة {o} حسب خصائص المشاركين"},
    "note_groups": {"en": "Test selected automatically from normality (Shapiro–Wilk) and homogeneity (Levene). * Significant at p < {a}.",
                    "ar": "اختير الاختبار آلياً بناءً على اعتدالية التوزيع (Shapiro–Wilk) وتجانس التباين (Levene). * دالّ عند p < {a}."},
    "p_groups_sig": {"en": "{o} differed significantly by {items}.", "ar": "وُجدت فروق ذات دلالة إحصائية في {o} حسب: {items}."},
    "p_groups_item": {"en": "{by} ({test}, {stat}, {p}; highest among '{hi}')",
                      "ar": "{by} ({stat}, {p}; {test}) وكانت الأعلى لدى فئة '{hi}'"},
    "p_groups_ns": {"en": "No statistically significant differences in {o} were found across the examined characteristics (all p ≥ {a}).",
                    "ar": "لم تُوجد فروق ذات دلالة إحصائية في {o} حسب الخصائص المدروسة (جميع قيم p ≥ {a})."},

    # ------------------------------------------------------------------ associations
    "h_assoc": {"en": "6. Factors associated with the outcome levels", "ar": "6. العوامل المرتبطة بمستويات المتغير التابع"},
    "cap_assoc": {"en": "Association between participant characteristics and {o}", "ar": "العلاقة بين خصائص المشاركين و{o}"},
    "note_assoc": {"en": "Row percentages. Pearson chi-square test; ᶠ Fisher's exact test. * p < {a}.",
                   "ar": "النسب المئوية حسب الصف. اختبار مربع كاي لبيرسون؛ ᶠ اختبار فيشر الدقيق. * p < {a}."},
    "p_assoc_sig": {"en": "{o} was significantly associated with {items}.", "ar": "ارتبط متغير {o} ارتباطاً دالاً إحصائياً بكلٍّ من: {items}."},
    "p_assoc_ns": {"en": "None of the characteristics were significantly associated with {o}.",
                   "ar": "لم ترتبط أيٌّ من الخصائص المدروسة ارتباطاً دالاً إحصائياً بمتغير {o}."},
    "cells_warn": {"en": "{pct}% of cells have expected count < 5 — consider merging categories or exact test",
                   "ar": "{pct}% من الخلايا تكرارها المتوقع < 5 — يُنصح بدمج الفئات أو استخدام اختبار دقيق"},

    # ------------------------------------------------------------------ correlations
    "h_corr": {"en": "7. Correlations between domains", "ar": "7. الارتباط بين المحاور"},
    "cap_corr": {"en": "Spearman's rank correlation coefficients between domain scores",
                 "ar": "معاملات ارتباط سبيرمان بين درجات المحاور"},
    "note_corr": {"en": "* p < {a}; ** p < 0.01.", "ar": "* p < {a}؛ ** p < 0.01."},
    "p_corr_sig": {"en": "Significant correlations were observed between {items}.",
                   "ar": "وُجدت ارتباطات ذات دلالة إحصائية بين: {items}."},
    "p_corr_item": {"en": "{a} and {b} ({strength} {dir}, rs = {r}, {p})",
                    "ar": "{a} و{b} بارتباط {dir} {strength} (rs = {r}, {p})"},
    "p_corr_ns": {"en": "No significant correlations were observed between the domain scores.",
                  "ar": "لم تُوجد ارتباطات ذات دلالة إحصائية بين درجات المحاور."},

    # ------------------------------------------------------------------ logistic
    "h_logit": {"en": "8. Predictors of the outcome (binary logistic regression)",
                "ar": "8. العوامل المنبئة بالمتغير التابع (الانحدار اللوجستي الثنائي)"},
    "cap_logit": {"en": "Binary logistic regression for predictors of {o} (event = '{e}')",
                  "ar": "نموذج الانحدار اللوجستي الثنائي للعوامل المنبئة بمتغير {o} (الحدث = '{e}')"},
    "note_logit": {"en": ("AOR, adjusted odds ratio; CI, confidence interval. Model χ²({df}) = {chi}, {p}; "
                          "Nagelkerke R² = {r2}; Hosmer–Lemeshow {hl}; correctly classified {acc}%. * p < {a}."),
                   "ar": ("AOR: نسبة الأرجحية المعدّلة؛ CI: فترة الثقة. النموذج: (χ²({df}) = {chi}, {p}; "
                          "Nagelkerke R² = {r2}; Hosmer–Lemeshow {hl})؛ نسبة التصنيف الصحيح {acc}%. * p < {a}.")},
    "p_logit_model_sig": {"en": "The multivariable model was statistically significant (χ²({df}) = {chi}, {p}; Nagelkerke R² = {r2}) and correctly classified {acc}% of cases. ",
                          "ar": "كان النموذج متعدد المتغيرات دالاً إحصائياً (χ²({df}) = {chi}, {p}; Nagelkerke R² = {r2})، وصنّف {acc}% من الحالات تصنيفاً صحيحاً. "},
    "p_logit_model_ns": {"en": "The multivariable model was not statistically significant (χ²({df}) = {chi}, {p}; Nagelkerke R² = {r2}) and correctly classified {acc}% of cases. ",
                         "ar": "لم يكن النموذج متعدد المتغيرات دالاً إحصائياً (χ²({df}) = {chi}, {p}; Nagelkerke R² = {r2})، وصنّف {acc}% من الحالات تصنيفاً صحيحاً. "},
    "p_logit_pred": {"en": "Independent predictors were: {items}.", "ar": "وكانت العوامل المنبئة المستقلة: {items}."},
    "p_logit_item": {"en": "{v} ({dir} odds; AOR = {aor}, 95% CI: {ci}, {p})",
                     "ar": "{v} بأرجحية {dir} (AOR = {aor}, 95% CI: {ci}, {p})"},
    "p_logit_none": {"en": "No predictor remained independently significant after adjustment.",
                     "ar": "لم يبقَ أيّ عامل دالاً إحصائياً بشكل مستقل بعد التعديل."},
    "higher": {"en": "higher", "ar": "أعلى"},
    "lower": {"en": "lower", "ar": "أقل"},
    "diag": {"en": "⚠ Model diagnostics: {items}.", "ar": "⚠ تشخيص النموذج: {items}."},
    "diag_epv": {"en": "events per variable = {epv} (< 10): risk of overfitting — reduce predictors",
                 "ar": "عدد الأحداث لكل متغير = {epv} (< 10): خطر الإفراط في الملاءمة — قلّل المتغيرات المنبئة"},
    "diag_hl": {"en": "Hosmer–Lemeshow p < 0.05: poor calibration", "ar": "Hosmer–Lemeshow p < 0.05: ضعف في معايرة النموذج"},
    "diag_or": {"en": "extreme ORs detected: check sparse categories / separation",
                "ar": "قيم OR متطرفة: راجع الفئات قليلة العدد أو مشكلة الانفصال التام"},
    "model_failed": {"en": "⚠ Model failed: {e}", "ar": "⚠ تعذّر تقدير النموذج: {e}"},
    "ref": {"en": "ref", "ar": "المرجع"},

    # ------------------------------------------------------------------ ROC
    "h_roc": {"en": "9. Discriminative ability (ROC curve analysis)", "ar": "9. القدرة التمييزية (تحليل منحنى ROC)"},
    "cap_roc": {"en": "Area under the ROC curve for predicting {o} (event = '{e}')",
                "ar": "المساحة تحت منحنى ROC للتنبؤ بمتغير {o} (الحدث = '{e}')"},
    "note_roc": {"en": ("Se, sensitivity; Sp, specificity; PPV/NPV, positive/negative predictive "
                        "value; LR, likelihood ratio. Optimal cut-off by maximum Youden index (J = Se + Sp − 1). "
                        "Se/Sp 95% CI by Wilson. Prevalence of event = {prev}%."),
                 "ar": ("Se: الحساسية؛ Sp: النوعية؛ PPV/NPV: القيمة التنبؤية الموجبة/السالبة؛ "
                        "LR: نسبة الاحتمال. حُدِّدت نقطة القطع المثلى بأعلى قيمة لمؤشر Youden (J = Se + Sp − 1). "
                        "فترات ثقة Se/Sp بطريقة Wilson. نسبة انتشار الحدث = {prev}%.")},
    "cap_roc_cut": {"en": "Diagnostic accuracy at the optimal cut-off points for predicting {o}",
                    "ar": "الدقة التشخيصية عند نقاط القطع المثلى للتنبؤ بمتغير {o}"},
    "note_roc_auc": {"en": "AUC, area under the curve; 95% CI by DeLong; p tests H0: AUC = 0.5. Interpretation per Hosmer & Lemeshow (0.7–0.8 acceptable, 0.8–0.9 excellent, ≥ 0.9 outstanding). * p < 0.05.",
                     "ar": "AUC: المساحة تحت المنحنى؛ فترة الثقة 95% بطريقة DeLong؛ تختبر قيمة p الفرضية AUC = 0.5. التفسير وفق Hosmer & Lemeshow (0.7–0.8 مقبولة، 0.8–0.9 ممتازة، ≥ 0.9 ممتازة جداً). * p < 0.05."},
    "cap_roc_cmp": {"en": "Pairwise comparison of AUCs (DeLong test)", "ar": "المقارنة الثنائية بين قيم AUC (اختبار DeLong)"},
    "cap_roc_fig": {"en": "ROC curves for predicting {o}", "ar": "منحنيات ROC للتنبؤ بمتغير {o}"},
    "cap_roc_coords": {"en": "ROC coordinates — {m}", "ar": "إحداثيات منحنى ROC — {m}"},
    "p_roc_item": {"en": ("{m} showed {lab} discrimination (AUC = {auc}, 95% CI: {ci}, {p}). At the optimal cut-off of "
                          "{cut}, sensitivity was {se}% and specificity {sp}% (Youden J = {j})."),
                   "ar": ("أظهر مؤشر {m} قدرة تمييزية {lab} (AUC = {auc}, 95% CI: {ci}, {p}). وعند نقطة القطع المثلى {cut} "
                          "بلغت الحساسية {se}% والنوعية {sp}% (Youden J = {j}).")},
    "p_roc_cmp": {"en": "The AUC of {a} was significantly different from that of {b} (ΔAUC = {d}, {p}).",
                  "ar": "اختلفت قيمة AUC لمؤشر {a} اختلافاً دالاً عن مؤشر {b} (ΔAUC = {d}, {p})."},
    "p_roc_cmp_ns": {"en": "No significant differences were found between the AUCs of the compared markers (DeLong test).",
                     "ar": "لم تُوجد فروق دالة إحصائياً بين قيم AUC للمؤشرات المقارنة (اختبار DeLong)."},
    "roc_inverse": {"en": "⚠ {m}: AUC < 0.5 — lower values predict the event; set \"direction\": {{\"{m}\": \"lower\"}}.",
                    "ar": "⚠ {m}: قيمة AUC < 0.5 — القيم الأقل هي المنبئة بالحدث؛ اضبط \"direction\": {{\"{m}\": \"lower\"}}."},
    "logit_model": {"en": "Logistic model (predicted probability)", "ar": "النموذج اللوجستي (الاحتمال المتنبأ)"},

    # ------------------------------------------------------------------ words
    "positive": {"en": "positive", "ar": "طردي"},
    "negative": {"en": "negative", "ar": "عكسي"},
}

WORDS_AR = {
    # alpha labels
    "excellent": "ممتاز", "good": "جيد", "acceptable": "مقبول", "questionable": "مشكوك فيه",
    "poor": "ضعيف", "unacceptable": "غير مقبول", "not computable": "غير قابل للحساب",
    # correlation strength
    "very strong": "قوي جداً", "strong": "قوي", "moderate": "متوسط", "weak": "ضعيف", "very weak": "ضعيف جداً",
    # kappa
    "almost perfect": "شبه تام", "substantial": "كبير", "fair": "مقبول", "slight": "طفيف",
    # tests
    "Independent t-test": "اختبار t للعينات المستقلة", "Welch's t-test": "اختبار Welch t",
    "Mann–Whitney U": "اختبار Mann–Whitney U", "One-way ANOVA": "تحليل التباين الأحادي ANOVA",
    "Welch's ANOVA": "تحليل Welch ANOVA", "Kruskal–Wallis H": "اختبار Kruskal–Wallis H",
    "Pearson χ²": "مربع كاي χ²", "Fisher's exact": "اختبار فيشر الدقيق",
}

AUC_AR = {"outstanding": "ممتازة جداً", "excellent": "ممتازة", "acceptable": "مقبولة",
          "poor": "ضعيفة", "fail": "منعدمة", "not computable": "غير قابلة للحساب"}

# Default Arabic display for common data values (extend per study with plan["value_labels_ar"])
VALUES_AR = {
    "Adequate": "كافية", "Inadequate": "غير كافية", "Yes": "نعم", "No": "لا",
    "Male": "ذكر", "Female": "أنثى", "Good": "جيد", "Moderate": "متوسط", "Poor": "ضعيف", "Fair": "مقبول",
    "Positive": "إيجابي", "Negative": "سلبي", "Neutral": "محايد", "High": "مرتفع", "Low": "منخفض",
    "Omani": "عُماني", "Non-Omani": "غير عُماني",
}

HEAD_AR = {
    "Variable": "المتغير", "Category": "الفئة", "n": "n", "%": "%",
    "Scale": "المحور", "No. of items": "عدد البنود", "Cronbach's α": "Cronbach's α", "Interpretation": "التفسير",
    "Domain": "المحور", "Possible range": "المدى الممكن", "Mean ± SD": "المتوسط ± الانحراف المعياري",
    "Median (IQR)": "الوسيط (المدى الربيعي)", "Item": "البند", "Test": "الاختبار", "Statistic": "قيمة الاختبار",
    "p": "p", "Effect size": "حجم الأثر", "χ² (df)": "χ² (df)", "Cramér's V": "Cramér's V",
    "Predictor": "المتغير المنبئ", "Crude OR": "OR غير المعدّلة", "Crude p": "p غير المعدّلة", "B": "B", "SE": "SE",
    "AOR": "AOR", "95% CI": "95% CI", "Marker": "المؤشر", "AUC (95% CI)": "AUC (95% CI)",
    "Discrimination": "القدرة التمييزية", "Cut-off": "نقطة القطع", "Se % (95% CI)": "الحساسية % (95% CI)",
    "Sp % (95% CI)": "النوعية % (95% CI)", "PPV %": "PPV %", "NPV %": "NPV %", "LR+": "LR+", "LR−": "LR−",
    "Youden J": "Youden J", "Comparison": "المقارنة", "ΔAUC": "ΔAUC", "z": "z",
    "Sensitivity": "الحساسية", "Specificity": "النوعية", "1 − Specificity": "1 − النوعية",
}


class Lang:
    def __init__(self, code: str = "en", var_labels: dict | None = None, value_labels_ar: dict | None = None):
        self.code = code if code in ("en", "ar") else "en"
        self.var_labels = var_labels or {}
        self.values_ar = {**VALUES_AR, **(value_labels_ar or {})}
        self.rtl = self.code == "ar"

    def __call__(self, key: str, **kw) -> str:
        return S[key][self.code].format(**kw)

    def w(self, word: str) -> str:
        """Translate a vocabulary word (labels, test names)."""
        return WORDS_AR.get(word, word) if self.rtl else word

    def auc(self, label: str) -> str:
        return AUC_AR.get(label, label) if self.rtl else label

    def val(self, x) -> str:
        """Display a data value / category (Arabic mapping in RTL mode)."""
        return self.values_ar.get(str(x), str(x)) if self.rtl else str(x)

    def v(self, var: str) -> str:
        """Display name of a variable (plan 'var_labels' may give {'en':..,'ar':..} or one string)."""
        lab = self.var_labels.get(var)
        if isinstance(lab, dict):
            return lab.get(self.code) or lab.get("en") or var.replace("_", " ")
        return lab or var.replace("_", " ")

    def head(self, col: str) -> str:
        if not self.rtl:
            return col
        if col in HEAD_AR:
            return HEAD_AR[col]
        if col.endswith(" n (%)"):
            return self.val(col[:-6]) + " n (%)"
        return col

    def comma(self) -> str:
        return "؛ " if self.rtl else "; "

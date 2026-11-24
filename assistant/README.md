# 🤖 المساعد الشخصي — AsaadStat Assistant

مساعد شخصي مبني على Claude Code، مُصمَّم حسب عمل أسعد الغافري: الإحصاء الصحي، دعم الباحثين، تقارير صنّاع القرار، ومشروع AsaadStat.

## كيف يعمل
1. **`CLAUDE.md`** (في جذر المستودع): ملف الهوية — يعرّف Claude بك، بأسلوبك المفضل، ومعايير التقرير الإحصائي. يُحمَّل تلقائياً في كل جلسة.
2. **أوامر `/` جاهزة** (`.claude/commands/`) لمهامك اليومية.
3. **محرك تحليل آلي** (`engine/`) — فكرة *Automated Research Analysis System* مُنفَّذة فعلياً.

## الأوامر
| الأمر | ماذا يفعل |
|---|---|
| `/analyze data.xlsx questionnaire.docx` | تحليل كامل آلي ← تقرير Word + جداول Excel + SPSS syntax |
| `/roc` | تحليل منحنى ROC: AUC، نقطة القطع (Youden)، الحساسية والنوعية، مقارنة DeLong |
| `/interpret` | تفسير مخرجات SPSS + فقرة جاهزة للنشر + تنبيهات الأخطاء |
| `/results` | كتابة قسم النتائج للمجلات المحكمة |
| `/spss` | توليد SPSS syntax جاهز للتشغيل |
| `/sample-size` | حساب حجم العينة + نص Methods |
| `/methodology` | تصميم منهجية بحث كاملة + خطة تحليل |
| `/stat-review` | مراجعة إحصائية لمخطوطة/رسالة كمحكّم |
| `/decision-brief` | موجز قرار للمديرية (Data → Decision) |
| `/client` | استقبال عميل AsaadStat: نطاق، سعر، مدة، رسالة رد |
| `/today` | خطة اليوم من `TASKS.md` |
| `/learn pandas groupby` | جلسة تعلم Python/SQL/SAS مربوطة بما تعرفه في SPSS |

## محرك التحليل الآلي
```bash
pip install pandas scipy statsmodels openpyxl python-docx tabulate matplotlib
python3 assistant/engine/auto_analysis.py assistant/examples/kap_plan.json            # حسب اللغات في الخطة
python3 assistant/engine/auto_analysis.py assistant/examples/kap_plan.json --lang ar  # عربي فقط
```
**المدخلات:** ملف بيانات (Excel/CSV) + خطة `plan.json` (المتغيرات الديموغرافية، المحاور وبنودها، البنود العكسية، نقاط القطع، المتغير التابع للانحدار).

**المخرجات** (في `assistant/output/`):
- `*_report.docx` / `*_report_ar.docx` — تقرير بجداول APA وفقرات تفسير بالإنجليزية و/أو بالعربية (RTL كامل: اتجاه الصفحة والجداول والفقرات)
- `*_roc.png` — منحنيات ROC (300 dpi تقريباً)
- `*_tables.xlsx` — كل جدول في ورقة
- `*_syntax.sps` — SPSS syntax مطابق للتحليل
- `*_scored_data.xlsx` — البيانات مع الدرجات والمستويات المحسوبة
- `*_summary.md` — ملخص يقرؤه Claude لمراجعة النتائج

**ما يحسبه تلقائياً:** التكرارات والنسب · Cronbach's α + α-if-deleted · درجات ومستويات KAP (Bloom) · اختيار الاختبار تلقائياً حسب التوزيع والتجانس (t / Welch / Mann-Whitney / ANOVA / Welch ANOVA / Kruskal-Wallis) مع حجم الأثر · Chi-square/Fisher مع Cramér's V وتنبيه الخلايا · Spearman · انحدار لوجستي (Crude OR + AOR، Nagelkerke، Hosmer-Lemeshow، EPV) · **تحليل ROC**: AUC مع فترة ثقة DeLong، نقطة القطع المثلى بمؤشر Youden، الحساسية والنوعية (فترات Wilson)، PPV/NPV، LR+/LR−، مقارنة DeLong بين المؤشرات، ومنحنى النموذج اللوجستي.

### التقرير العربي
أضف في الخطة:
```json
"languages": ["en", "ar"],
"title_ar": "عنوان الدراسة بالعربية",
"var_labels": {"gender": {"en": "Gender", "ar": "الجنس"}},
"value_labels_ar": {"Bachelor": "بكالوريوس"}
```
النصوص العربية كلها في `engine/i18n.py` — عدّل الصياغة من هناك. الرموز الإحصائية والأرقام تبقى بالحروف اللاتينية (المعتاد في التقارير الخليجية).

### ROC
```json
"roc": {"outcome": "Practice_adequate", "event": "Adequate",
        "markers": ["Knowledge_score", "Attitude_score"],
        "direction": {"Attitude_score": "higher"},
        "include_logistic_model": true}
```

أدوات إضافية في `stats_core.py`: Cohen's Kappa + PABAK. و`sample_size.py`: نسبة واحدة (Cochran + FPC)، نسبتان، متوسطان، ارتباط، انحدار لوجستي (EPV).

مثال جاهز: `examples/sample_output/` (بيانات KAP تجريبية مُولَّدة، وليست حقيقية).

## الخصوصية
مجلد `clients/` و`output/` مستبعدان من git — لا تُرفع بيانات المرضى أو المشاركين أبداً.

## خصّصه
- عدّل الأسعار في `knowledge/pricing.md` (حالياً فارغة).
- أضف مهامك في `TASKS.md`.
- عدّل `CLAUDE.md` إذا تغيّرت تفضيلاتك.

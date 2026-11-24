"""Regression tests for the AsaadStat analysis engine.

Run:  python3 -m pytest assistant/tests -q
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ENGINE = Path(__file__).resolve().parents[1] / "engine"
sys.path.insert(0, str(ENGINE))
import auto_analysis as aa  # noqa: E402
import stats_core as sc  # noqa: E402


@pytest.fixture
def spss_like():
    """0/1 outcome with missing values → pandas reads it as float (1.0/0.0/NaN)."""
    rng = np.random.default_rng(1)
    n = 200
    df = pd.DataFrame({"sex": rng.choice([1, 2], n), "score": rng.normal(50, 10, n)})
    y = (df.score + rng.normal(0, 8, n) > 52).astype(float)
    y[:5] = np.nan
    df["outcome"] = y
    return df


# ------------------------------------------------------------------ value matching
@pytest.mark.parametrize("value, event", [(1.0, 1), (1, "1"), ("1", 1.0), ("Yes", "Yes"), (2.0, "2")])
def test_matches_event_across_types(value, event):
    assert sc.is_event(pd.Series([value]), event).iloc[0] == 1.0


def test_is_event_keeps_missing_as_nan():
    out = sc.is_event(pd.Series([1.0, 0.0, np.nan]), 1)
    assert out.iloc[0] == 1 and out.iloc[1] == 0 and np.isnan(out.iloc[2])


# ------------------------------------------------------------------ bug 1: float outcome with NaN
def test_logistic_with_float_outcome_and_missing(spss_like):
    r = sc.logistic_regression(spss_like, "outcome", ["sex", "score"], event=1)
    assert "error" not in r
    assert r["events"] > 50
    row = r["table"].set_index("Predictor").loc["score"]   # AOR per 1-point increase in score
    assert 1.05 < row["AOR"] < 2 and row["p"] < 0.001


def test_roc_section_with_float_outcome_and_missing(spss_like, tmp_path):
    spss_like.to_excel(tmp_path / "d.xlsx", index=False)
    plan = {"project": "T", "data": "d.xlsx", "output_dir": ".", "item_tables": False,
            "roc": {"outcome": "outcome", "event": 1, "markers": ["score"]}}
    (tmp_path / "p.json").write_text(json.dumps(plan))
    aa.run(str(tmp_path / "p.json"), ["en"])
    md = (tmp_path / "T_summary.md").read_text(encoding="utf-8")
    assert "AUC = 0." in md and "need ≥2 events" not in md


# ------------------------------------------------------------------ bug 2: no crash on bad models
def test_logistic_unknown_reference_returns_clear_error():
    rng = np.random.default_rng(0)
    d = pd.DataFrame({"y": rng.integers(0, 2, 120), "edu": rng.choice(["Diploma", "Bachelor"], 120),
                      "x": rng.normal(size=120)})
    r = sc.logistic_regression(d, "y", ["edu", "x"], 1, {"edu": "diploma"})
    assert "error" in r and "diploma" in r["error"] and "Diploma" in r["error"]


def test_logistic_perfect_separation_does_not_raise():
    d = pd.DataFrame({"y": [0] * 20 + [1] * 20, "x": list(range(40))})
    r = sc.logistic_regression(d, "y", ["x"], 1)
    assert isinstance(r, dict)  # either a result with inf-safe CI or an error message — never an exception


def test_logistic_no_events_returns_error():
    d = pd.DataFrame({"y": [0] * 30, "x": np.arange(30.0)})
    r = sc.logistic_regression(d, "y", ["x"], 1)
    assert "error" in r


# ------------------------------------------------------------------ bug 3: Excel export with no tables
def test_pipeline_with_no_tables_writes_all_outputs(tmp_path):
    pd.DataFrame({"outcome": [0] * 10, "score": range(10)}).to_excel(tmp_path / "d.xlsx", index=False)
    plan = {"project": "E", "data": "d.xlsx", "output_dir": ".", "item_tables": False,
            "roc": {"outcome": "outcome", "event": 1, "markers": ["score"]}}
    (tmp_path / "p.json").write_text(json.dumps(plan))
    aa.run(str(tmp_path / "p.json"), ["en"])
    for suffix in ("_report.docx", "_tables.xlsx", "_summary.md", "_syntax.sps", "_scored_data.xlsx"):
        assert (tmp_path / f"E{suffix}").exists(), suffix


# ------------------------------------------------------------------ bug 4: mixed-type categories
def test_frequency_table_mixed_types():
    ft = sc.frequency_table(pd.DataFrame({"job": [1, 2, "other", 1, 2, np.nan]}), ["job"])
    assert set(ft.Category) >= {"1", "2", "other", "Missing"}


def test_item_tables_mixed_types(tmp_path):
    df = pd.DataFrame({"K1": [1, 0, "dk", 1, 0, 1], "K2": [1, 1, 0, 0, 1, 1]})
    df.to_excel(tmp_path / "d.xlsx", index=False)
    plan = {"project": "M", "data": "d.xlsx", "output_dir": ".",
            "scales": {"K": {"items": ["K1", "K2"], "item_min": 0, "item_max": 1}}}
    (tmp_path / "p.json").write_text(json.dumps(plan))
    aa.run(str(tmp_path / "p.json"), ["en"])
    assert (tmp_path / "M_report.docx").exists()


# ------------------------------------------------------------------ bug 6: recode on float columns
def test_recode_float_column_with_missing(tmp_path):
    pd.DataFrame({"K1": [1, 0, np.nan, 1]}).to_excel(tmp_path / "r.xlsx", index=False)
    df = aa.load_data({"data": "r.xlsx", "recode": {"K1": {"1": "Correct", "0": "Wrong"}}}, tmp_path)
    assert df.K1.tolist()[:2] == ["Correct", "Wrong"] and pd.isna(df.K1.iloc[2])


# ------------------------------------------------------------------ demo still works end to end
def test_demo_plan_runs(tmp_path):
    src = Path(__file__).resolve().parents[1] / "examples"
    plan = json.loads((src / "kap_plan.json").read_text(encoding="utf-8"))
    plan["data"] = str(src / "demo_kap_data.xlsx")
    plan["output_dir"] = str(tmp_path)
    (tmp_path / "p.json").write_text(json.dumps(plan, ensure_ascii=False), encoding="utf-8")
    aa.run(str(tmp_path / "p.json"), ["en", "ar"])
    md = (tmp_path / f"{plan['project']}_summary.md").read_text(encoding="utf-8")
    assert "AUC = 0.851" in md and "AOR = 1.76" in md

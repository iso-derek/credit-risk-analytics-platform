"""JSON API for the credit risk web app.

Every number comes from the tested analysis code in ``src/``; this module only
shapes results for the screens and attaches plain-English field names.

Run for development:  .venv/Scripts/python -m uvicorn api.main:app --reload
"""
from __future__ import annotations

import json
import sys
import threading
from functools import lru_cache
from pathlib import Path
from typing import Literal

import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from analytics import applicant_explanation, concentration_summary, missingness_summary, segment_loss_summary  # noqa: E402
from data_sources import download_german_credit, download_public_credit, synthetic_dataset  # noqa: E402
from modelling import applicant_sensitivity, model_feature_importance, score_band, train_credit_models  # noqa: E402
from monitoring import feature_drift_table, score_drift_summary  # noqa: E402
from research import compare_selections, loss_scenarios, result_bundle  # noqa: E402
from subgroup import add_audit_groups, add_intersection_group, available_group_columns, subgroup_diagnostics  # noqa: E402

from api.fields import describe, label  # noqa: E402

Dataset = Literal["synthetic", "uci", "german"]
LOADERS = {"synthetic": synthetic_dataset, "uci": download_public_credit, "german": download_german_credit}
BANDS = ["A (<5%)", "B (5–10%)", "C (10–18%)", "D (18–30%)", "E (30%+)"]
BAND_NAMES = {"A (<5%)": "Very low", "B (5–10%)": "Low", "C (10–18%)": "Moderate", "D (18–30%)": "High", "E (30%+)": "Very high"}
SEGMENT_FIELDS = ["credit_score_band", "loan_purpose", "employment_status", "home_ownership", "purpose", "housing", "job", "checking_account"]
METRIC_INFO = {
    "roc_auc": {"label": "Ranking accuracy (ROC AUC)", "kind": "ratio", "better": "higher",
                "help": "How well the model ranks defaulters above non-defaulters. 0.5 is a coin flip, 1.0 is perfect."},
    "pr_auc": {"label": "Precision–recall AUC", "kind": "ratio", "better": "higher",
               "help": "Ranking quality focused on the applicants who actually default."},
    "brier": {"label": "Brier score", "kind": "ratio", "better": "lower",
              "help": "Average squared gap between predicted probability and outcome. Lower is better."},
    "log_loss": {"label": "Log loss", "kind": "ratio", "better": "lower",
                 "help": "Penalises confident wrong predictions. Lower is better; used to pick the model."},
    "loss_proxy_error": {"label": "Expected-loss error", "kind": "percent", "better": "lower",
                         "help": "Gap between predicted and observed loss under the assumed 45% loss rate."},
}

app = FastAPI(title="Credit Risk API", version="1.0.0")
_study_lock = threading.Lock()


@lru_cache(maxsize=2)
def _study(dataset: str) -> dict:
    df, spec = LOADERS[dataset]()
    return train_credit_models(df, spec)


def study(dataset: Dataset) -> dict:
    with _study_lock:
        try:
            return _study(dataset)
        except (ValueError, OSError, RuntimeError) as exc:
            raise HTTPException(status_code=503, detail=f"The dataset could not be loaded: {exc}") from exc


def records(frame: pd.DataFrame) -> list[dict]:
    """JSON-safe records (NaN → null, numpy → Python)."""
    return json.loads(frame.to_json(orient="records", date_format="iso"))


def scalar(value):
    """Convert one numpy/pandas value to plain JSON (missing → None)."""
    if isinstance(value, (bool, np.bool_)):
        return bool(value)
    if isinstance(value, (int, np.integer)):
        return int(value)
    if isinstance(value, (float, np.floating)):
        return float(value) if np.isfinite(value) else None
    if value is None or value is pd.NA or value is pd.NaT:
        return None
    return str(value)


def band_info(band: str) -> dict:
    return {"band": band, "letter": band[:1], "name": BAND_NAMES.get(band, band), "range": band[3:-1] if "(" in band else band}


# ---------------------------------------------------------------- meta / overview
@app.get("/api/meta")
def meta(dataset: Dataset = "synthetic"):
    result = study(dataset)
    spec = result["spec"]
    features = spec["numeric"] + spec["categorical"]
    return {
        "dataset": dataset,
        "synthetic": bool(spec["synthetic"]),
        "name": {"synthetic": "Simulated applicants", "uci": "Taiwan credit-card clients (UCI)", "german": "German Credit (UCI Statlog)"}[dataset],
        "source_url": spec.get("source_url"),
        "protected_fields": [label(f) for f in spec.get("protected_fields", ["SEX", "EDUCATION", "MARRIAGE", "AGE"] if dataset == "uci" else [])],
        "source": spec["source"],
        "currency": spec["currency"],
        "outcome": spec["target_horizon"],
        "exposure_assumption": spec["exposure_assumption"],
        "lgd": 0.45,
        "model": result["best_model_name"],
        "test_applicants": int(len(result["scored_data"])),
        "fields": [describe(name) for name in features],
        "bands": [band_info(band) for band in BANDS],
    }


@app.get("/api/overview")
def overview(dataset: Dataset = "synthetic"):
    result = study(dataset)
    df = result["scored_data"]
    bins = np.linspace(0, 1, 21)
    df_bins = pd.cut(df.probability_default, bins, include_lowest=True, labels=False)
    histogram = []
    for index in range(20):
        in_bin = df[df_bins == index]
        row = {"from": float(bins[index]), "to": float(bins[index + 1])}
        for band in BANDS:
            row[band[:1]] = int((in_bin.credit_score_band == band).sum())
        histogram.append(row)
    bands = []
    for band in BANDS:
        rows = df[df.credit_score_band == band]
        bands.append({**band_info(band), "applicants": int(len(rows)),
                      "share": float(len(rows) / len(df)),
                      "mean_pd": scalar(rows.probability_default.mean()) if len(rows) else None,
                      "observed_default_rate": scalar(rows.default.mean()) if len(rows) else None,
                      "exposure": float(rows.ead.sum()), "expected_loss": float(rows.expected_loss.sum())})
    return {
        "kpis": {
            "applicants": int(len(df)),
            "mean_pd": float(df.probability_default.mean()),
            "observed_default_rate": float(df.default.mean()),
            "exposure": float(df.ead.sum()),
            "expected_loss": float(df.expected_loss.sum()),
        },
        "histogram": histogram,
        "bands": bands,
        "segment_options": [{"key": key, "label": label(key)} for key in SEGMENT_FIELDS
                            if key in df and df[key].nunique(dropna=False) > 1],
    }


@app.get("/api/segments")
def segments(by: str = "loan_purpose", dataset: Dataset = "synthetic"):
    df = study(dataset)["scored_data"]
    if by not in SEGMENT_FIELDS or by not in df:
        raise HTTPException(status_code=400, detail="Choose a supported segment.")
    table = segment_loss_summary(df, by)
    return {"by": by, "label": label(by), "rows": records(table), "concentration": concentration_summary(table)}


@app.get("/api/coverage")
def coverage(dataset: Dataset = "synthetic"):
    result = study(dataset)
    spec = result["spec"]
    table = missingness_summary(result["scored_data"], spec["numeric"] + spec["categorical"])
    table["field"] = table.field.map(label)
    return {"rows": records(table.drop(columns=["data_type"]))}


# ---------------------------------------------------------------- applicants
@app.get("/api/applicants")
def applicants(
    dataset: Dataset = "synthetic",
    search: str = "",
    band: str = "",
    sort: Literal["risk", "loss", "exposure", "id"] = "risk",
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    df = study(dataset)["scored_data"]
    view = df
    if search:
        needle = search.strip().lower()
        text_columns = [c for c in ["application_id", "loan_purpose", "employment_status", "home_ownership", "purpose", "job", "housing"] if c in df]
        mask = np.zeros(len(df), dtype=bool)
        for column in text_columns:
            mask |= df[column].astype(str).str.lower().str.contains(needle, regex=False).to_numpy()
        view = view[mask]
    if band:
        view = view[view.credit_score_band.str.startswith(band)]
    order = {"risk": ("probability_default", False), "loss": ("expected_loss", False),
             "exposure": ("ead", False), "id": ("application_id", True)}[sort]
    view = view.sort_values(order[0], ascending=order[1])
    columns = [c for c in ["application_id", "credit_score_band", "probability_default", "ead", "expected_loss",
                           "loan_purpose", "purpose", "employment_status", "job", "annual_income", "fico_score", "age", "AGE", "LIMIT_BAL"] if c in view]
    page = view.iloc[offset:offset + limit][columns]
    return {"total": int(len(view)), "rows": records(page)}


@app.get("/api/applicants/{application_id}")
def applicant(application_id: str, dataset: Dataset = "synthetic"):
    result = study(dataset)
    df, spec = result["scored_data"], result["spec"]
    match = df[df.application_id.astype(str) == application_id]
    if match.empty:
        raise HTTPException(status_code=404, detail="No held-out applicant has that ID.")
    row = match.iloc[0]
    features = spec["numeric"] + spec["categorical"]
    sensitivity = applicant_sensitivity(result, row).head(8)
    drivers = []
    for item in sensitivity.itertuples(index=False):
        drivers.append({**describe(item.feature), "value": scalar(row[item.feature]),
                        "reference": scalar(result["reference"][item.feature]), "pd_change": float(item.pd_change)})
    return {
        "application_id": str(row.application_id),
        "probability_default": float(row.probability_default),
        **band_info(row.credit_score_band),
        "exposure": float(row.ead),
        "expected_loss": float(row.expected_loss),
        "defaulted": bool(row.default),
        "summary": applicant_explanation(row) if spec["synthetic"] else None,
        "profile": [{**describe(name), "value": scalar(row[name])} for name in features],
        "drivers": drivers,
    }


# ---------------------------------------------------------------- scenarios
@app.get("/api/scenario")
def scenario(
    dataset: Dataset = "synthetic",
    odds: float = Query(1.0, gt=0, le=10),
    lgd: float = Query(0.45, ge=0, le=1),
    exposure: float = Query(1.0, ge=0, le=5),
):
    df = study(dataset)["scored_data"]
    table = loss_scenarios(df, odds, lgd, exposure)
    baseline_loss = float(df.expected_loss.sum())
    scenario_loss = float(table.scenario_expected_loss.sum())
    shifted = table.scenario_pd.map(score_band)
    bands = [{**band_info(band), "baseline": int((df.credit_score_band == band).sum()),
              "scenario": int((shifted == band).sum())} for band in BANDS]
    return {
        "baseline": {"expected_loss": baseline_loss, "mean_pd": float(df.probability_default.mean()),
                     "exposure": float(df.ead.sum())},
        "scenario": {"expected_loss": scenario_loss, "mean_pd": float(table.scenario_pd.mean()),
                     "exposure": float(table.scenario_exposure.sum())},
        "change": scenario_loss - baseline_loss,
        "bands": bands,
    }


# ---------------------------------------------------------------- model evidence
@app.get("/api/models")
def models(dataset: Dataset = "synthetic"):
    result = study(dataset)
    rows = []
    for name, metrics in result["models"].items():
        algorithm, variant = (name.split(" / ") + [""])[:2]
        rows.append({"name": name, "algorithm": algorithm, "variant": variant.capitalize(),
                     "selected": name == result["best_model_name"], "best_ranking": name == result["ranking_model_name"],
                     **{key: float(metrics[key]) for key in METRIC_INFO}})
    reliability = records(result["reliability"].rename(columns={"predicted_pd": "predicted", "observed_default_rate": "observed"}))
    return {
        "selected": result["best_model_name"],
        "best_ranking": result["ranking_model_name"],
        "metrics": [{"key": key, **info} for key, info in METRIC_INFO.items()],
        "models": rows,
        "reliability": reliability,
        "selection_test": compare_selections(result),
    }


@app.get("/api/models/importance")
def importance(dataset: Dataset = "synthetic"):
    table = model_feature_importance(study(dataset))
    return {"rows": [{**describe(row.feature), "importance": float(row.importance), "spread": float(row.standard_deviation)}
                     for row in table.itertuples(index=False)]}


@app.get("/api/drift")
def drift(dataset: Dataset = "synthetic"):
    result = study(dataset)
    spec, df = result["spec"], result["scored_data"]
    table = feature_drift_table(result["reference_X"], df, spec["numeric"], spec["categorical"])
    score = score_drift_summary(result["reference_scores"], df.probability_default)
    features = [{**describe(row["feature"]), "psi": scalar(row["psi"]), "signal": row["shift_signal"],
                 "type": row["feature_type"].capitalize()} for row in table.to_dict("records")]
    return {"score": {key: scalar(value) for key, value in score.items()}, "features": features}


# ---------------------------------------------------------------- fairness
@app.get("/api/fairness")
def fairness(
    dataset: Dataset = "synthetic",
    group: str = "",
    second: str = "",
    threshold: float = Query(0.20, ge=0.05, le=0.8),
    min_size: int = Query(30, ge=10, le=200),
):
    result = study(dataset)
    frame = add_audit_groups(result["scored_data"])
    options = available_group_columns(frame)
    if not options:
        return {"options": [], "rows": []}
    group = group or options[0]
    if group not in options or (second and second not in options):
        raise HTTPException(status_code=400, detail="Choose a supported group.")
    column = group
    if second:
        try:
            frame = add_intersection_group(frame, group, second)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        column = "intersection"
    table = subgroup_diagnostics(frame, column, threshold, min_size, bootstrap_draws=500, seed=result["seed"])
    return {"options": [{"key": key, "label": label(key)} for key in options],
            "group": group, "second": second or None, "rows": records(table)}


# ---------------------------------------------------------------- downloads
def _csv(frame: pd.DataFrame, filename: str) -> Response:
    return Response(frame.to_csv(index=False), media_type="text/csv",
                    headers={"Content-Disposition": f'attachment; filename="{filename}"'})


@app.get("/api/downloads/{kind}")
def download(kind: Literal["applicants", "scenario", "drift", "research"], dataset: Dataset = "synthetic",
             odds: float = 1.0, lgd: float = 0.45, exposure: float = 1.0):
    result = study(dataset)
    df = result["scored_data"]
    if kind == "applicants":
        return _csv(df, "credit_applicants.csv")
    if kind == "scenario":
        try:
            return _csv(loss_scenarios(df, odds, lgd, exposure), "credit_scenario.csv")
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
    if kind == "drift":
        spec = result["spec"]
        return _csv(feature_drift_table(result["reference_X"], df, spec["numeric"], spec["categorical"]), "credit_drift.csv")
    return Response(result_bundle(result), media_type="application/zip",
                    headers={"Content-Disposition": 'attachment; filename="credit_research.zip"'})


@app.get("/api/health")
def health():
    return {"status": "ok"}


# ---------------------------------------------------------------- web app (production build)
WEB_DIST = ROOT / "web" / "dist"
if WEB_DIST.exists():
    app.mount("/assets", StaticFiles(directory=WEB_DIST / "assets"), name="assets")

    @app.get("/{path:path}", include_in_schema=False)
    def spa(path: str):
        candidate = (WEB_DIST / path).resolve()
        if path and candidate.is_file() and WEB_DIST.resolve() in candidate.parents:
            return FileResponse(candidate)
        return FileResponse(WEB_DIST / "index.html")

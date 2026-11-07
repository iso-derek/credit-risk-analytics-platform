"""Credit portfolio analytics."""

from __future__ import annotations

import pandas as pd
import numpy as np


def portfolio_summary(df: pd.DataFrame) -> dict[str, float]:
    return {
        "applications": float(len(df)),
        "total_exposure": float(df["ead"].sum()),
        "average_pd": float(df["probability_default"].mean()),
        "expected_loss": float(df["expected_loss"].sum()),
        "observed_default_rate": float(df["default"].mean()) if "default" in df else 0.0,
    }


def band_summary(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.groupby("credit_score_band", as_index=False)
        .agg(applications=("application_id", "count"), total_exposure=("ead", "sum"), avg_pd=("probability_default", "mean"), expected_loss=("expected_loss", "sum"))
        .sort_values("credit_score_band")
    )


def purpose_summary(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.groupby("loan_purpose", as_index=False)
        .agg(applications=("application_id", "count"), avg_pd=("probability_default", "mean"), expected_loss=("expected_loss", "sum"))
        .sort_values("expected_loss", ascending=False)
    )


def applicant_explanation(row: pd.Series) -> str:
    reasons = []
    if row.get("fico_score", 850) < 620:
        reasons.append("low FICO score")
    if row.get("debt_to_income", 0) >= 0.40:
        reasons.append("high debt-to-income")
    if row.get("credit_utilisation", 0) >= 0.65:
        reasons.append("high credit utilisation")
    if row.get("num_delinquencies", 0) >= 2:
        reasons.append("recent delinquencies")
    if row.get("recent_inquiries", 0) >= 4:
        reasons.append("high recent credit inquiries")
    if not reasons:
        return "Risk mainly driven by model interactions rather than a single rule."
    return "Applicant risk driven by " + ", ".join(reasons) + "."


def missingness_summary(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    """Describe raw held-out field coverage before pipeline imputation."""
    missing = set(columns) - set(df)
    if missing:
        raise ValueError(f"Missing portfolio fields: {sorted(missing)}")
    if not len(df):
        raise ValueError("Portfolio must contain at least one applicant.")
    rows = []
    for column in columns:
        count = int(df[column].isna().sum())
        rows.append({
            "field": column,
            "data_type": str(df[column].dtype),
            "missing_applicants": count,
            "missing_rate": count / len(df),
            "coverage_status": "Complete" if count == 0 else "Pipeline imputes missing values",
        })
    return pd.DataFrame(rows).sort_values(["missing_rate", "field"], ascending=[False, True], ignore_index=True)


def segment_loss_summary(df: pd.DataFrame, group_column: str) -> pd.DataFrame:
    """Aggregate exposure and expected loss without changing applicant scores."""
    required = {group_column, "application_id", "probability_default", "ead", "expected_loss"}
    missing = required - set(df)
    if missing:
        raise ValueError(f"Missing segment fields: {sorted(missing)}")
    if not len(df):
        raise ValueError("Portfolio must contain at least one applicant.")
    if not np.isfinite(df[["probability_default", "ead", "expected_loss"]].to_numpy(float)).all():
        raise ValueError("Portfolio probabilities, exposure and expected loss must be finite.")
    if (df[["ead", "expected_loss"]] < 0).any().any():
        raise ValueError("Exposure and expected loss must be non-negative.")
    frame = df.assign(**{group_column: df[group_column].astype("string").fillna("Missing")})
    aggregations = {
        "applicants": ("application_id", "count"),
        "total_exposure": ("ead", "sum"),
        "mean_predicted_pd": ("probability_default", "mean"),
        "expected_loss": ("expected_loss", "sum"),
    }
    if "default" in frame:
        aggregations["observed_default_rate"] = ("default", "mean")
    result = frame.groupby(group_column, as_index=False, dropna=False).agg(**aggregations)
    result = result.rename(columns={group_column: "segment"})
    result["applicant_share"] = result.applicants / result.applicants.sum()
    exposure_total = result.total_exposure.sum()
    loss_total = result.expected_loss.sum()
    result["exposure_share"] = result.total_exposure / exposure_total if exposure_total else 0.0
    result["expected_loss_share"] = result.expected_loss / loss_total if loss_total else 0.0
    return result.sort_values(["expected_loss", "segment"], ascending=[False, True], ignore_index=True)


def concentration_summary(segments: pd.DataFrame) -> dict[str, float]:
    """Return descriptive concentration measures for a segment aggregation."""
    required = {"exposure_share", "expected_loss_share"}
    if required - set(segments) or segments.empty:
        raise ValueError("A non-empty segment summary with share columns is required.")
    return {
        "segments": float(len(segments)),
        "largest_exposure_share": float(segments.exposure_share.max()),
        "largest_expected_loss_share": float(segments.expected_loss_share.max()),
        "exposure_hhi": float(np.square(segments.exposure_share).sum()),
        "expected_loss_hhi": float(np.square(segments.expected_loss_share).sum()),
    }

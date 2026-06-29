"""Credit portfolio analytics."""

from __future__ import annotations

import pandas as pd


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

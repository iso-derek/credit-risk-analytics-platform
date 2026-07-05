"""Credit portfolio analytics."""

from __future__ import annotations

import pandas as pd

from explainability import risk_reason_generator


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
    return risk_reason_generator(row)

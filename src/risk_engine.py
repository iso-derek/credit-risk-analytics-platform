"""Professional credit risk metrics and portfolio analytics."""

from __future__ import annotations

import numpy as np
import pandas as pd


def risk_grade(probability_default: float) -> str:
    """Map probability of default to an internal risk grade."""

    if probability_default < 0.03:
        return "Grade 1 - Prime"
    if probability_default < 0.07:
        return "Grade 2 - Strong"
    if probability_default < 0.12:
        return "Grade 3 - Acceptable"
    if probability_default < 0.20:
        return "Grade 4 - Watchlist"
    if probability_default < 0.35:
        return "Grade 5 - High Risk"
    return "Grade 6 - Very High Risk"


def enrich_risk_metrics(df: pd.DataFrame, lgd: float = 0.45) -> pd.DataFrame:
    """Add banking-style credit risk metrics to a scored dataframe."""

    enriched = df.copy()
    enriched["pd"] = enriched["probability_default"]
    enriched["lgd"] = enriched.get("lgd", lgd)
    enriched["ead"] = enriched.get("ead", enriched["loan_amount"])
    enriched["expected_loss"] = enriched["pd"] * enriched["lgd"] * enriched["ead"]
    enriched["risk_grade"] = enriched["pd"].apply(risk_grade)
    enriched["risk_band"] = enriched["credit_score_band"]
    enriched["delinquency_flag"] = (enriched["num_delinquencies"] > 0).astype(int)
    enriched["high_utilisation_flag"] = (enriched["credit_utilisation"] >= 0.65).astype(int)
    return enriched


def portfolio_risk_summary(df: pd.DataFrame) -> dict[str, float]:
    """Return executive credit portfolio metrics."""

    if df.empty:
        return {
            "applications": 0,
            "total_ead": 0,
            "average_pd": 0,
            "expected_loss": 0,
            "expected_loss_rate": 0,
            "default_rate": 0,
            "delinquency_rate": 0,
        }
    total_ead = float(df["ead"].sum())
    expected_loss = float(df["expected_loss"].sum())
    return {
        "applications": float(len(df)),
        "total_ead": total_ead,
        "average_pd": float(df["pd"].mean()),
        "expected_loss": expected_loss,
        "expected_loss_rate": expected_loss / total_ead if total_ead else 0,
        "default_rate": float(df["default"].mean()) if "default" in df else 0,
        "delinquency_rate": float((df["num_delinquencies"] > 0).mean()) if "num_delinquencies" in df else 0,
    }


def risk_band_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Summarise PD, EAD and expected loss by risk band."""

    return (
        df.groupby(["risk_band", "risk_grade"], as_index=False)
        .agg(
            applications=("application_id", "count"),
            default_rate=("default", "mean"),
            average_pd=("pd", "mean"),
            total_ead=("ead", "sum"),
            expected_loss=("expected_loss", "sum"),
        )
        .sort_values("average_pd")
    )


def delinquency_analysis(df: pd.DataFrame) -> pd.DataFrame:
    """Summarise risk by delinquency count."""

    buckets = pd.cut(
        df["num_delinquencies"],
        bins=[-1, 0, 1, 2, np.inf],
        labels=["0", "1", "2", "3+"],
    )
    return (
        df.assign(delinquency_bucket=buckets)
        .groupby("delinquency_bucket", observed=False, as_index=False)
        .agg(
            applications=("application_id", "count"),
            default_rate=("default", "mean"),
            average_pd=("pd", "mean"),
            expected_loss=("expected_loss", "sum"),
        )
    )


def lift_table(y_true: pd.Series | np.ndarray, probabilities: np.ndarray, bins: int = 10) -> pd.DataFrame:
    """Build a decile lift table for default ranking quality."""

    frame = pd.DataFrame({"actual_default": np.asarray(y_true), "pd": probabilities})
    frame["decile"] = pd.qcut(frame["pd"].rank(method="first"), q=bins, labels=False) + 1
    summary = (
        frame.groupby("decile", as_index=False)
        .agg(applications=("actual_default", "count"), defaults=("actual_default", "sum"), average_pd=("pd", "mean"))
        .sort_values("decile", ascending=False)
    )
    portfolio_default_rate = frame["actual_default"].mean()
    summary["default_rate"] = summary["defaults"] / summary["applications"]
    summary["lift"] = summary["default_rate"] / portfolio_default_rate if portfolio_default_rate else 0
    return summary


def business_risk_narrative(summary: dict[str, float]) -> str:
    """Generate a business-readable portfolio risk summary."""

    return (
        f"The portfolio contains {summary['applications']:,.0f} applications with "
        f"{summary['total_ead']:,.0f} total EAD. Average PD is {summary['average_pd']:.2%}, "
        f"expected loss rate is {summary['expected_loss_rate']:.2%}, and observed default rate is "
        f"{summary['default_rate']:.2%}. Delinquency rate is {summary['delinquency_rate']:.2%}."
    )

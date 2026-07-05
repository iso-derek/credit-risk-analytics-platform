"""Explainable AI helpers for credit risk models."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from preprocessing import feature_columns


def shap_available() -> bool:
    """Return whether SHAP is installed in the current environment."""

    try:
        import shap  # noqa: F401

        return True
    except Exception:
        return False


def global_feature_importance(result: dict[str, Any], top_n: int = 20) -> pd.DataFrame:
    """Return model-level feature importance using coefficients or tree importances."""

    pipeline = result["best_pipeline"]
    model = pipeline.named_steps["model"]
    preprocessor = pipeline.named_steps["preprocessor"]
    try:
        names = preprocessor.get_feature_names_out()
    except Exception:
        names = np.array(feature_columns())
    if hasattr(model, "feature_importances_"):
        values = model.feature_importances_
    elif hasattr(model, "coef_"):
        values = np.abs(model.coef_[0])
    else:
        values = np.zeros(len(names))
    return (
        pd.DataFrame({"feature": names, "importance": values})
        .sort_values("importance", ascending=False)
        .head(top_n)
        .reset_index(drop=True)
    )


def local_reason_codes(row: pd.Series) -> list[str]:
    """Generate local business reason codes for one applicant."""

    reasons: list[str] = []
    if row.get("fico_score", 850) < 620:
        reasons.append("low FICO score")
    if row.get("debt_to_income", 0) >= 0.40:
        reasons.append("high debt-to-income ratio")
    if row.get("credit_utilisation", 0) >= 0.65:
        reasons.append("high revolving credit utilisation")
    if row.get("num_delinquencies", 0) >= 2:
        reasons.append("previous delinquencies")
    if row.get("recent_inquiries", 0) >= 4:
        reasons.append("high recent credit inquiries")
    if row.get("credit_history_years", 99) < 2:
        reasons.append("short credit history")
    if row.get("loan_to_income", 0) >= 0.6:
        reasons.append("large loan size relative to income")
    return reasons


def risk_reason_generator(row: pd.Series) -> str:
    """Return a natural-language applicant risk explanation."""

    reasons = local_reason_codes(row)
    if not reasons:
        return "This applicant has lower observed rule-based risk drivers; model risk is mainly driven by feature interactions."
    if len(reasons) == 1:
        reason_text = reasons[0]
    else:
        reason_text = ", ".join(reasons[:-1]) + f" and {reasons[-1]}"
    return f"This applicant has elevated default risk because of {reason_text}."


def local_customer_explanation(row: pd.Series) -> dict[str, Any]:
    """Return structured local explanation fields for one applicant."""

    return {
        "application_id": row.get("application_id", ""),
        "probability_default": float(row.get("probability_default", 0)),
        "risk_band": row.get("credit_score_band", ""),
        "risk_grade": row.get("risk_grade", ""),
        "reason_codes": local_reason_codes(row),
        "explanation": risk_reason_generator(row),
    }


def shap_summary_frame(result: dict[str, Any], sample: pd.DataFrame, max_rows: int = 250) -> pd.DataFrame:
    """Return a SHAP summary frame when SHAP is installed, otherwise an empty frame."""

    if not shap_available() or sample.empty:
        return pd.DataFrame(columns=["feature", "mean_abs_shap"])
    import shap

    pipeline = result["best_pipeline"]
    transformed = pipeline.named_steps["preprocessor"].transform(sample[feature_columns()].head(max_rows))
    model = pipeline.named_steps["model"]
    try:
        explainer = shap.Explainer(model, transformed)
        values = explainer(transformed)
        mean_abs = np.abs(values.values).mean(axis=0)
    except Exception:
        return pd.DataFrame(columns=["feature", "mean_abs_shap"])

    try:
        feature_names = pipeline.named_steps["preprocessor"].get_feature_names_out()
    except Exception:
        feature_names = np.array(feature_columns())
    return (
        pd.DataFrame({"feature": feature_names, "mean_abs_shap": mean_abs})
        .sort_values("mean_abs_shap", ascending=False)
        .head(20)
        .reset_index(drop=True)
    )

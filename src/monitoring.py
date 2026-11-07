"""Descriptive cohort-shift diagnostics with fixed reference-derived bins."""
from __future__ import annotations

import numpy as np
import pandas as pd


def _psi(reference_labels: pd.Series, current_labels: pd.Series, categories: list[str], epsilon: float) -> float:
    ref = reference_labels.value_counts(normalize=True).reindex(categories, fill_value=0).to_numpy(float)
    cur = current_labels.value_counts(normalize=True).reindex(categories, fill_value=0).to_numpy(float)
    ref = np.maximum(ref, epsilon); cur = np.maximum(cur, epsilon)
    ref /= ref.sum(); cur /= cur.sum()
    return float(np.sum((cur - ref) * np.log(cur / ref)))


def numeric_psi(reference: pd.Series, current: pd.Series, bins: int = 10, epsilon: float = 1e-6) -> float:
    """Population Stability Index using quantile edges fixed on the reference cohort."""
    if bins < 2 or not 0 < epsilon < .1:
        raise ValueError("Use at least two bins and epsilon in (0, 0.1).")
    ref = pd.to_numeric(reference, errors="coerce")
    cur = pd.to_numeric(current, errors="coerce")
    finite_ref = ref[np.isfinite(ref)]
    if finite_ref.empty:
        raise ValueError("Numeric reference requires at least one finite value.")
    quantiles = np.unique(np.quantile(finite_ref, np.linspace(0, 1, bins + 1)))
    if len(quantiles) <= 1:
        ref_labels = pd.Series(np.where(ref.isna(), "Missing", "Constant"), index=ref.index)
        cur_labels = pd.Series(np.where(cur.isna(), "Missing", np.where(cur == quantiles[0], "Constant", "Other")), index=cur.index)
        return _psi(ref_labels, cur_labels, ["Constant", "Other", "Missing"], epsilon)
    edges = np.concatenate(([-np.inf], quantiles[1:-1], [np.inf]))
    labels = [f"bin_{index}" for index in range(len(edges) - 1)]
    ref_labels = pd.cut(ref, edges, labels=labels, include_lowest=True).astype("string").fillna("Missing")
    cur_labels = pd.cut(cur, edges, labels=labels, include_lowest=True).astype("string").fillna("Missing")
    return _psi(ref_labels, cur_labels, labels + ["Missing"], epsilon)


def categorical_psi(reference: pd.Series, current: pd.Series, epsilon: float = 1e-6) -> float:
    """PSI over reference categories, an explicit unseen bucket, and missing values."""
    if not 0 < epsilon < .1:
        raise ValueError("Epsilon must lie in (0, 0.1).")
    ref = reference.astype("string").fillna("Missing")
    cur = current.astype("string").fillna("Missing")
    known = sorted(value for value in ref.unique().tolist() if value != "Missing")
    ref_labels = ref.where(ref.isin(known + ["Missing"]), "Unseen")
    cur_labels = cur.where(cur.isin(known + ["Missing"]), "Unseen")
    return _psi(ref_labels, cur_labels, known + ["Unseen", "Missing"], epsilon)


def drift_interpretation(psi: float) -> str:
    if psi < .1:
        return "Lower shift signal"
    if psi < .25:
        return "Moderate shift signal"
    return "Higher shift signal"


def feature_drift_table(
    reference: pd.DataFrame,
    current: pd.DataFrame,
    numeric: list[str],
    categorical: list[str],
    bins: int = 10,
) -> pd.DataFrame:
    """Compare predictor distributions without using current outcome labels."""
    columns = numeric + categorical
    missing = set(columns) - set(reference) | (set(columns) - set(current))
    if missing:
        raise ValueError(f"Missing drift fields: {sorted(missing)}")
    if len(reference) < 2 or len(current) < 2:
        raise ValueError("Reference and current cohorts each require at least two rows.")
    rows = []
    for column in columns:
        psi = numeric_psi(reference[column], current[column], bins) if column in numeric else categorical_psi(reference[column], current[column])
        rows.append({
            "feature": column,
            "feature_type": "Numeric" if column in numeric else "Categorical",
            "psi": psi,
            "shift_signal": drift_interpretation(psi),
            "reference_missing_rate": float(reference[column].isna().mean()),
            "current_missing_rate": float(current[column].isna().mean()),
            "missing_rate_change": float(current[column].isna().mean() - reference[column].isna().mean()),
        })
    return pd.DataFrame(rows).sort_values(["psi", "feature"], ascending=[False, True], ignore_index=True)


def score_drift_summary(reference_scores, current_scores, bins: int = 10) -> dict[str, float | str]:
    reference = pd.Series(np.asarray(reference_scores, dtype=float))
    current = pd.Series(np.asarray(current_scores, dtype=float))
    if reference.empty or current.empty or not np.isfinite(reference).all() or not np.isfinite(current).all():
        raise ValueError("Score cohorts must be non-empty and finite.")
    if ((reference < 0) | (reference > 1)).any() or ((current < 0) | (current > 1)).any():
        raise ValueError("Scores must lie within [0, 1].")
    psi = numeric_psi(reference, current, bins)
    return {
        "psi": psi,
        "shift_signal": drift_interpretation(psi),
        "reference_mean_pd": float(reference.mean()),
        "current_mean_pd": float(current.mean()),
        "mean_pd_change": float(current.mean() - reference.mean()),
    }

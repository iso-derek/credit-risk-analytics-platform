"""Held-out subgroup diagnostics for model research, not compliance certification."""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.metrics import brier_score_loss, roc_auc_score


def add_audit_groups(scored: pd.DataFrame) -> pd.DataFrame:
    """Return a copy with a coarse age band when age is available."""
    frame = scored.copy()
    age_column = "age" if "age" in frame else "AGE" if "AGE" in frame else None
    if age_column:
        frame["age_band"] = pd.cut(
            pd.to_numeric(frame[age_column], errors="coerce"),
            bins=[0, 29, 39, 49, 59, np.inf],
            labels=["Under 30", "30–39", "40–49", "50–59", "60+"],
        )
    return frame


def available_group_columns(scored: pd.DataFrame) -> list[str]:
    """Expose intentional evaluation fields, never arbitrary high-cardinality IDs."""
    candidates = [
        "employment_status", "home_ownership", "loan_purpose", "age_band",
        "SEX", "EDUCATION", "MARRIAGE",
    ]
    frame = add_audit_groups(scored)
    return [column for column in candidates if column in frame and frame[column].nunique(dropna=True) > 1]


def _bootstrap_intervals(y: np.ndarray, p: np.ndarray, draws: int, seed: int) -> tuple[float, float, float, float]:
    rng = np.random.default_rng(seed)
    observed, gaps = np.empty(draws), np.empty(draws)
    for draw in range(draws):
        sample = rng.integers(0, len(y), len(y))
        observed[draw] = y[sample].mean()
        gaps[draw] = p[sample].mean() - observed[draw]
    return (*np.quantile(observed, [.025, .975]), *np.quantile(gaps, [.025, .975]))


def subgroup_diagnostics(
    scored: pd.DataFrame,
    group_column: str,
    threshold: float = .20,
    min_group_size: int = 30,
    bootstrap_draws: int = 500,
    seed: int = 42,
) -> pd.DataFrame:
    """Compute conditional held-out diagnostics with explicit suppression rules."""
    if not 0 < threshold < 1:
        raise ValueError("Threshold must lie strictly between 0 and 1.")
    if min_group_size < 2:
        raise ValueError("Minimum group size must be at least 2.")
    if bootstrap_draws < 100:
        raise ValueError("Use at least 100 bootstrap draws.")
    frame = add_audit_groups(scored)
    required = {group_column, "default", "probability_default"}
    missing = required - set(frame)
    if missing:
        raise ValueError(f"Missing subgroup fields: {sorted(missing)}")

    rows = []
    grouped = frame.assign(**{group_column: frame[group_column].astype("string").fillna("Missing")}).groupby(group_column, dropna=False)
    for position, (group, values) in enumerate(grouped):
        y = values["default"].to_numpy(dtype=int)
        p = values["probability_default"].to_numpy(dtype=float)
        if not np.isfinite(p).all() or ((p < 0) | (p > 1)).any() or not set(np.unique(y)).issubset({0, 1}):
            raise ValueError("Outcomes must be binary and probabilities finite within [0, 1].")
        row = {"group": str(group), "applicants": len(values), "defaults": int(y.sum())}
        if len(values) < min_group_size:
            rows.append({**row, "status": "Suppressed: below minimum sample"})
            continue
        if len(np.unique(y)) < 2:
            rows.append({**row, "status": "Suppressed: one observed outcome"})
            continue
        flagged = p >= threshold
        tp = int(np.sum(flagged & (y == 1))); fp = int(np.sum(flagged & (y == 0)))
        positives = int(y.sum()); negatives = len(y) - positives
        observed_lo, observed_hi, gap_lo, gap_hi = _bootstrap_intervals(y, p, bootstrap_draws, seed + position)
        row.update({
            "status": "Reported", "mean_predicted_pd": float(p.mean()),
            "observed_default_rate": float(y.mean()), "observed_rate_ci_low": observed_lo,
            "observed_rate_ci_high": observed_hi, "calibration_gap": float(p.mean() - y.mean()),
            "calibration_gap_ci_low": gap_lo, "calibration_gap_ci_high": gap_hi,
            "brier_score": float(brier_score_loss(y, p)), "roc_auc": float(roc_auc_score(y, p)),
            "flag_rate": float(flagged.mean()), "true_positive_rate": tp / positives,
            "false_positive_rate": fp / negatives,
            "precision": tp / max(int(flagged.sum()), 1),
        })
        rows.append(row)
    return pd.DataFrame(rows).sort_values(["status", "applicants", "group"], ascending=[False, False, True], ignore_index=True)

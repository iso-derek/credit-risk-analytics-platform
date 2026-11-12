"""Operational contracts for timestamped monitoring cohorts and alert routing."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import json

import numpy as np
import pandas as pd


DEFAULT_POLICY_PATH = Path(__file__).resolve().parents[1] / "config" / "monitoring_policy.json"


def load_monitoring_policy(path: Path | str = DEFAULT_POLICY_PATH) -> dict:
    policy = json.loads(Path(path).read_text(encoding="utf-8"))
    required = {"policy_version", "minimum_cohort_rows", "outcome_lag_days", "thresholds", "owners"}
    missing = required - set(policy)
    if missing:
        raise ValueError(f"Monitoring policy is missing: {sorted(missing)}")
    thresholds = policy["thresholds"]
    if not 0 < thresholds["moderate_psi"] < thresholds["high_psi"]:
        raise ValueError("PSI thresholds must be positive and increasing.")
    if not 0 < thresholds["missing_rate_change"] <= 1:
        raise ValueError("Missing-rate threshold must lie in (0, 1].")
    if policy["minimum_cohort_rows"] < 2 or policy["outcome_lag_days"] < 0:
        raise ValueError("Cohort size must be at least two and outcome lag cannot be negative.")
    for role in ("model_risk", "data_quality", "engineering"):
        if not str(policy["owners"].get(role, "")).strip():
            raise ValueError(f"Monitoring policy requires an owner role for {role}.")
    return policy


def _as_utc(value) -> pd.Timestamp:
    timestamp = pd.Timestamp(value)
    if timestamp.tzinfo is None:
        timestamp = timestamp.tz_localize("UTC")
    return timestamp.tz_convert("UTC")


def validate_timestamped_cohort(
    cohort: pd.DataFrame,
    required_features: list[str],
    *,
    as_of: datetime | str | pd.Timestamp | None = None,
    timestamp_column: str = "observed_at",
    id_column: str = "application_id",
    minimum_rows: int = 2,
) -> dict:
    """Validate an immutable scoring cohort boundary without inspecting outcomes."""
    required = set(required_features) | {timestamp_column, id_column}
    missing = required - set(cohort)
    if missing:
        raise ValueError(f"Monitoring cohort is missing: {sorted(missing)}")
    if len(cohort) < minimum_rows:
        raise ValueError(f"Monitoring cohort requires at least {minimum_rows} rows.")
    if cohort[id_column].isna().any() or cohort[id_column].duplicated().any():
        raise ValueError("Monitoring cohort IDs must be unique and non-missing.")
    timestamps = pd.to_datetime(cohort[timestamp_column], utc=True, errors="coerce")
    if timestamps.isna().any():
        raise ValueError("Monitoring timestamps must be valid and timezone-aware or UTC-assumed.")
    cutoff = _as_utc(as_of or datetime.now(timezone.utc))
    if (timestamps > cutoff).any():
        raise ValueError("Monitoring cohort contains observations after the as-of timestamp.")
    return {
        "row_count": int(len(cohort)),
        "unique_ids": int(cohort[id_column].nunique()),
        "cohort_start_utc": timestamps.min().isoformat(),
        "cohort_end_utc": timestamps.max().isoformat(),
        "as_of_utc": cutoff.isoformat(),
        "feature_count": len(required_features),
    }


def outcome_maturity_summary(
    cohort: pd.DataFrame,
    *,
    as_of: datetime | str | pd.Timestamp,
    outcome_lag_days: int,
    timestamp_column: str = "observed_at",
    outcome_column: str = "default",
) -> dict:
    """Separate outcome-eligible rows from immature rows before performance review."""
    if outcome_lag_days < 0:
        raise ValueError("Outcome lag cannot be negative.")
    missing = {timestamp_column, outcome_column} - set(cohort)
    if missing:
        raise ValueError(f"Outcome review is missing: {sorted(missing)}")
    timestamps = pd.to_datetime(cohort[timestamp_column], utc=True, errors="coerce")
    if timestamps.isna().any():
        raise ValueError("Outcome review timestamps must be valid.")
    cutoff = _as_utc(as_of) - pd.Timedelta(days=outcome_lag_days)
    eligible = timestamps <= cutoff
    labels = pd.to_numeric(cohort[outcome_column], errors="coerce")
    invalid = labels.dropna()[~labels.dropna().isin([0, 1])]
    if not invalid.empty:
        raise ValueError("Observed outcomes must be binary when present.")
    matured_labels = labels[eligible]
    available = matured_labels.notna()
    eligible_count = int(eligible.sum())
    return {
        "outcome_cutoff_utc": cutoff.isoformat(),
        "eligible_rows": eligible_count,
        "immature_rows": int((~eligible).sum()),
        "eligible_labels_available": int(available.sum()),
        "eligible_labels_missing": int(eligible_count - available.sum()),
        "eligible_label_coverage": float(available.mean()) if eligible_count else None,
    }


def route_monitoring_signals(feature_drift: pd.DataFrame, score_drift: dict, policy: dict) -> pd.DataFrame:
    """Create an owned triage register; signals never trigger automatic model action."""
    required = {"feature", "psi", "missing_rate_change"}
    missing = required - set(feature_drift)
    if missing:
        raise ValueError(f"Feature drift table is missing: {sorted(missing)}")
    moderate = float(policy["thresholds"]["moderate_psi"])
    high = float(policy["thresholds"]["high_psi"])
    missing_limit = float(policy["thresholds"]["missing_rate_change"])
    rows = []

    def add(signal, value, severity, owner_key, action):
        rows.append({"signal": signal, "value": float(value), "severity": severity,
                     "owner": policy["owners"][owner_key], "required_action": action})

    for item in feature_drift.itertuples(index=False):
        if not np.isfinite(item.psi) or not np.isfinite(item.missing_rate_change):
            raise ValueError("Monitoring signals must be finite.")
        if item.psi >= high:
            add(f"feature_psi:{item.feature}", item.psi, "High", "model_risk", "Investigate source and impact; document disposition.")
        elif item.psi >= moderate:
            add(f"feature_psi:{item.feature}", item.psi, "Moderate", "model_risk", "Review alongside volume, mix and data-quality evidence.")
        if abs(item.missing_rate_change) >= missing_limit:
            add(f"missing_rate_change:{item.feature}", item.missing_rate_change, "High", "data_quality", "Trace upstream completeness change and remediate or accept.")
    score_psi = float(score_drift["psi"])
    if not np.isfinite(score_psi):
        raise ValueError("Score PSI must be finite.")
    if score_psi >= moderate:
        severity = "High" if score_psi >= high else "Moderate"
        add("score_psi", score_psi, severity, "model_risk", "Review score mix; do not recalibrate without approved evidence.")
    return pd.DataFrame(rows, columns=["signal", "value", "severity", "owner", "required_action"])

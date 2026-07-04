"""Credit dataset validation and quality reporting."""

from __future__ import annotations

import pandas as pd


REQUIRED_COLUMNS = [
    "application_id",
    "age",
    "annual_income",
    "loan_amount",
    "loan_term_months",
    "interest_rate",
    "debt_to_income",
    "fico_score",
    "credit_history_years",
    "credit_utilisation",
    "num_delinquencies",
    "recent_inquiries",
    "open_accounts",
    "employment_status",
    "home_ownership",
    "loan_purpose",
    "default",
]


def missing_columns(df: pd.DataFrame, required_columns: list[str] | None = None) -> list[str]:
    """Return required columns missing from a dataframe."""

    required = required_columns or REQUIRED_COLUMNS
    return [column for column in required if column not in df.columns]


def duplicate_count(df: pd.DataFrame, key: str = "application_id") -> int:
    """Count duplicate application IDs if the key exists."""

    if key not in df.columns:
        return 0
    return int(df.duplicated(subset=[key]).sum())


def missing_value_report(df: pd.DataFrame) -> pd.DataFrame:
    """Return missing value counts and percentages for non-complete columns."""

    if df.empty:
        return pd.DataFrame(columns=["column", "missing_count", "missing_pct"])
    report = df.isna().sum().reset_index()
    report.columns = ["column", "missing_count"]
    report["missing_pct"] = report["missing_count"] / len(df)
    return report[report["missing_count"] > 0].sort_values("missing_count", ascending=False)


def validate_credit_dataset(df: pd.DataFrame) -> list[str]:
    """Return human-readable data quality warnings."""

    warnings: list[str] = []
    missing = missing_columns(df)
    if missing:
        warnings.append(f"Missing required columns: {', '.join(missing)}")
    duplicates = duplicate_count(df)
    if duplicates:
        warnings.append(f"Duplicate application IDs detected: {duplicates}")
    missing_values = missing_value_report(df)
    if not missing_values.empty:
        warnings.append(f"Columns with missing values: {len(missing_values)}")
    return warnings


def prepare_credit_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """Apply light schema cleanup while preserving raw credit fields."""

    prepared = df.copy()
    if "application_id" not in prepared.columns:
        prepared.insert(0, "application_id", [f"APP{idx:07d}" for idx in range(1, len(prepared) + 1)])
    prepared = prepared.drop_duplicates(subset=["application_id"], keep="first")
    for column in REQUIRED_COLUMNS:
        if column not in prepared.columns:
            prepared[column] = pd.NA
    return prepared[REQUIRED_COLUMNS]

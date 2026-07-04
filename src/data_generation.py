"""Synthetic loan portfolio data generation."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from config import DEFAULT_SYNTHETIC_PATH, RAW_DIR, configured_credit_data_path
from data_quality import prepare_credit_dataset, validate_credit_dataset

RAW_PATH = DEFAULT_SYNTHETIC_PATH


def generate_credit_data(n_rows: int = 15000, seed: int = 42) -> pd.DataFrame:
    """Generate a synthetic credit risk dataset with realistic risk drivers."""
    rng = np.random.default_rng(seed)
    employment = rng.choice(["Employed", "Self-employed", "Student", "Unemployed", "Retired"], n_rows, p=[0.58, 0.18, 0.07, 0.08, 0.09])
    home = rng.choice(["Mortgage", "Rent", "Own", "Other"], n_rows, p=[0.42, 0.36, 0.18, 0.04])
    purpose = rng.choice(["Debt consolidation", "Car", "Home improvement", "Education", "Business", "Medical", "Other"], n_rows)
    income = np.clip(rng.lognormal(10.75, 0.55, n_rows), 12000, 240000)
    loan_amount = np.clip(rng.lognormal(9.7, 0.65, n_rows), 1000, 65000)
    interest_rate = np.clip(rng.normal(0.105, 0.045, n_rows), 0.035, 0.29)
    credit_history_years = np.clip(rng.gamma(4.5, 2.3, n_rows), 0.2, 35)
    delinquencies = rng.poisson(0.35, n_rows)
    credit_utilisation = np.clip(rng.beta(2.2, 4.5, n_rows), 0.02, 0.98)
    inquiries = rng.poisson(1.2, n_rows)
    open_accounts = np.clip(rng.poisson(7, n_rows) + 1, 1, 35)
    dti = np.clip((loan_amount / income) + rng.normal(0.18, 0.09, n_rows), 0.02, 0.85)
    fico = np.clip(735 - 95 * credit_utilisation - 12 * delinquencies - 4 * inquiries + rng.normal(0, 38, n_rows), 480, 850)

    employment_risk = pd.Series(employment).map({"Employed": -0.25, "Self-employed": 0.05, "Student": 0.2, "Unemployed": 0.8, "Retired": 0.05}).to_numpy()
    home_risk = pd.Series(home).map({"Mortgage": -0.15, "Own": -0.25, "Rent": 0.15, "Other": 0.3}).to_numpy()
    logit = (
        -3.2
        + 3.4 * dti
        + 2.5 * credit_utilisation
        + 0.18 * delinquencies
        + 0.08 * inquiries
        + 5.5 * interest_rate
        - 0.006 * (fico - 650)
        - 0.025 * credit_history_years
        + employment_risk
        + home_risk
    )
    pd_true = 1 / (1 + np.exp(-logit))
    default = rng.binomial(1, np.clip(pd_true, 0.01, 0.85))

    df = pd.DataFrame(
        {
            "application_id": [f"APP{idx:07d}" for idx in range(1, n_rows + 1)],
            "age": rng.integers(21, 72, n_rows),
            "annual_income": income.round(2),
            "loan_amount": loan_amount.round(2),
            "loan_term_months": rng.choice([24, 36, 48, 60, 72], n_rows, p=[0.12, 0.36, 0.2, 0.24, 0.08]),
            "interest_rate": interest_rate.round(4),
            "debt_to_income": dti.round(4),
            "fico_score": fico.round(0).astype(int),
            "credit_history_years": credit_history_years.round(1),
            "credit_utilisation": credit_utilisation.round(4),
            "num_delinquencies": delinquencies,
            "recent_inquiries": inquiries,
            "open_accounts": open_accounts,
            "employment_status": employment,
            "home_ownership": home,
            "loan_purpose": purpose,
            "default": default,
        }
    )
    return df


def save_credit_data(path: Path = RAW_PATH) -> pd.DataFrame:
    path.parent.mkdir(parents=True, exist_ok=True)
    df = generate_credit_data()
    df.to_csv(path, index=False)
    return df


def load_public_credit_data(path: Path | None = None) -> tuple[pd.DataFrame | None, list[str]]:
    """Load a configured public credit dataset if it exists and matches the schema."""

    dataset_path = path or configured_credit_data_path()
    if not dataset_path.exists():
        return None, [f"External credit dataset not found: {dataset_path}"]

    df = pd.read_csv(dataset_path)
    warnings = validate_credit_dataset(df)
    if any(warning.startswith("Missing required columns") for warning in warnings):
        return None, warnings
    return prepare_credit_dataset(df), warnings


def load_or_create_credit_data(path: Path = RAW_PATH, external_path: Path | None = None) -> pd.DataFrame:
    """Load external public data when available, otherwise use synthetic fallback data."""

    external_df, _warnings = load_public_credit_data(external_path)
    if external_df is not None:
        return external_df
    if path.exists():
        return prepare_credit_dataset(pd.read_csv(path))
    return save_credit_data(path)


def data_source_status(external_path: Path | None = None) -> dict[str, object]:
    """Return metadata describing which dataset source is active."""

    configured_path = external_path or configured_credit_data_path()
    external_df, warnings = load_public_credit_data(configured_path)
    if external_df is not None:
        return {"source": str(configured_path), "rows": len(external_df), "warnings": warnings, "fallback": False}
    fallback = load_or_create_credit_data()
    return {"source": str(RAW_PATH), "rows": len(fallback), "warnings": warnings, "fallback": True}


if __name__ == "__main__":
    data = save_credit_data()
    print(f"Saved {len(data):,} loan applications to {RAW_PATH}")

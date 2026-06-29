"""Preprocessing and feature engineering for credit risk models."""

from __future__ import annotations

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


NUMERIC_FEATURES = [
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
    "loan_to_income",
    "risk_rule_score",
]

CATEGORICAL_FEATURES = ["employment_status", "home_ownership", "loan_purpose"]


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["loan_to_income"] = df["loan_amount"] / df["annual_income"].replace(0, pd.NA)
    df["high_dti_flag"] = (df["debt_to_income"] >= 0.40).astype(int)
    df["high_utilisation_flag"] = (df["credit_utilisation"] >= 0.65).astype(int)
    df["thin_file_flag"] = (df["credit_history_years"] < 2).astype(int)
    df["recent_credit_seeking_flag"] = (df["recent_inquiries"] >= 4).astype(int)
    df["subprime_flag"] = (df["fico_score"] < 620).astype(int)
    df["risk_rule_score"] = (
        df["high_dti_flag"]
        + df["high_utilisation_flag"]
        + df["thin_file_flag"]
        + df["recent_credit_seeking_flag"]
        + df["subprime_flag"] * 2
        + (df["num_delinquencies"] >= 2).astype(int) * 2
    )
    return df


def build_preprocessor() -> ColumnTransformer:
    numeric_pipeline = Pipeline([("imputer", SimpleImputer(strategy="median")), ("scaler", StandardScaler())])
    categorical_pipeline = Pipeline([("imputer", SimpleImputer(strategy="most_frequent")), ("onehot", OneHotEncoder(handle_unknown="ignore"))])
    return ColumnTransformer(
        transformers=[
            ("numeric", numeric_pipeline, NUMERIC_FEATURES),
            ("categorical", categorical_pipeline, CATEGORICAL_FEATURES),
        ]
    )


def feature_columns() -> list[str]:
    return NUMERIC_FEATURES + CATEGORICAL_FEATURES

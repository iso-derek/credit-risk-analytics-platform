"""Plotly chart helpers for credit risk analytics."""

from __future__ import annotations

import pandas as pd
import plotly.express as px


def pd_distribution(df: pd.DataFrame):
    return px.histogram(df, x="probability_default", color="credit_score_band", nbins=50, title="Probability of Default Distribution")


def expected_loss_by_band(df: pd.DataFrame):
    grouped = df.groupby("credit_score_band", as_index=False)["expected_loss"].sum()
    return px.bar(grouped, x="credit_score_band", y="expected_loss", title="Expected Loss by Credit Score Band")


def feature_importance_chart(importance: pd.DataFrame):
    return px.bar(importance.sort_values("importance"), x="importance", y="feature", orientation="h", title="Feature Importance")

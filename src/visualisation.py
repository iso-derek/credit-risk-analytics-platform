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


def risk_grade_distribution(df: pd.DataFrame):
    grouped = df.groupby("risk_grade", as_index=False).agg(applications=("application_id", "count"), expected_loss=("expected_loss", "sum"))
    return px.bar(grouped, x="risk_grade", y="applications", color="expected_loss", title="Applications by Risk Grade")


def roc_curve_chart(curve: pd.DataFrame):
    return px.line(curve, x="fpr", y="tpr", title="ROC Curve", labels={"fpr": "False Positive Rate", "tpr": "True Positive Rate"})


def precision_recall_chart(curve: pd.DataFrame):
    return px.line(curve, x="recall", y="precision", title="Precision-Recall Curve")


def calibration_chart(curve: pd.DataFrame):
    return px.line(curve, x="mean_predicted_pd", y="observed_default_rate", markers=True, title="Calibration Curve")


def lift_chart(lift: pd.DataFrame):
    return px.bar(lift, x="decile", y="lift", title="Decile Lift Chart", labels={"decile": "Risk decile", "lift": "Lift vs portfolio default rate"})

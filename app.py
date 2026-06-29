"""Streamlit dashboard for credit risk analytics."""

from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd
import streamlit as st
import plotly.express as px


PROJECT_ROOT = Path(__file__).resolve().parent
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.append(str(SRC_DIR))

from analytics import applicant_explanation, band_summary, portfolio_summary, purpose_summary  # noqa: E402
from data_generation import load_or_create_credit_data  # noqa: E402
from modelling import model_feature_importance, train_credit_models  # noqa: E402
from visualisation import expected_loss_by_band, feature_importance_chart, pd_distribution  # noqa: E402


st.set_page_config(page_title="Credit Risk Analytics Platform", layout="wide")


@st.cache_data(show_spinner=True)
def get_model_result():
    return train_credit_models(load_or_create_credit_data())


st.title("Credit Risk Analytics Platform")
st.caption("Synthetic credit portfolio for education, analytics, and model demonstration. Not a lending decision engine.")

result = get_model_result()
df = result["scored_data"].copy()
df["risk_explanation"] = df.apply(applicant_explanation, axis=1)
summary = portfolio_summary(df)

st.subheader("Portfolio Risk Summary")
cols = st.columns(5)
cols[0].metric("Applications", f"{summary['applications']:,.0f}")
cols[1].metric("Total Exposure", f"${summary['total_exposure']:,.0f}")
cols[2].metric("Average PD", f"{summary['average_pd']:.2%}")
cols[3].metric("Expected Loss", f"${summary['expected_loss']:,.0f}")
cols[4].metric("Best Model", result["best_model_name"])

tab1, tab2, tab3, tab4 = st.tabs(["Risk Dashboard", "Applicant Explorer", "Model Explanation", "Data"])

with tab1:
    left, right = st.columns(2)
    left.plotly_chart(pd_distribution(df), width="stretch")
    right.plotly_chart(expected_loss_by_band(df), width="stretch")
    st.plotly_chart(px.bar(purpose_summary(df), x="loan_purpose", y="expected_loss", title="Expected Loss by Loan Purpose"), width="stretch")
    st.dataframe(band_summary(df).style.format({"total_exposure": "${:,.0f}", "avg_pd": "{:.2%}", "expected_loss": "${:,.0f}"}), width="stretch", hide_index=True)

with tab2:
    band_filter = st.multiselect("Credit score band", sorted(df["credit_score_band"].unique()))
    explorer = df[df["credit_score_band"].isin(band_filter)] if band_filter else df
    columns = ["application_id", "credit_score_band", "probability_default", "expected_loss", "fico_score", "debt_to_income", "credit_utilisation", "loan_amount", "risk_explanation"]
    st.dataframe(explorer[columns].sort_values("probability_default", ascending=False).head(500).style.format({"probability_default": "{:.2%}", "expected_loss": "${:,.0f}", "debt_to_income": "{:.2%}", "credit_utilisation": "{:.2%}", "loan_amount": "${:,.0f}"}), width="stretch", hide_index=True)

with tab3:
    best = result["models"][result["best_model_name"]]
    st.write(f"ROC-AUC: **{best['roc_auc']:.3f}**, Precision: **{best['precision']:.3f}**, Recall: **{best['recall']:.3f}**")
    cm = pd.DataFrame(best["confusion_matrix"], index=["Actual non-default", "Actual default"], columns=["Predicted non-default", "Predicted default"])
    st.dataframe(cm, width="stretch")
    importance = model_feature_importance(result)
    st.plotly_chart(feature_importance_chart(importance), width="stretch")
    st.write("SHAP can be added as an optional enhancement; this version uses model feature importance for lightweight explainability.")

with tab4:
    st.dataframe(df.head(100), width="stretch")

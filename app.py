"""Streamlit dashboard for credit risk analytics."""

from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd
import plotly.express as px
import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parent
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.append(str(SRC_DIR))

from analytics import band_summary, purpose_summary  # noqa: E402
from data_generation import data_source_status, load_or_create_credit_data  # noqa: E402
from explainability import global_feature_importance, local_customer_explanation, shap_available, shap_summary_frame  # noqa: E402
from modelling import train_credit_models  # noqa: E402
from risk_engine import business_risk_narrative, delinquency_analysis, portfolio_risk_summary, risk_band_summary  # noqa: E402
from visualisation import (  # noqa: E402
    calibration_chart,
    expected_loss_by_band,
    feature_importance_chart,
    lift_chart,
    pd_distribution,
    precision_recall_chart,
    risk_grade_distribution,
    roc_curve_chart,
)


st.set_page_config(page_title="Credit Risk Analytics Platform", layout="wide")


@st.cache_data(show_spinner=True)
def get_model_result() -> dict[str, object]:
    return train_credit_models(load_or_create_credit_data())


def format_currency(value: float) -> str:
    return f"${value:,.0f}"


def render_sidebar(df: pd.DataFrame) -> tuple[str, pd.DataFrame]:
    st.sidebar.title("Credit Risk Platform")
    page = st.sidebar.radio(
        "Navigate",
        ["Portfolio Overview", "Applicant Explorer", "Model Performance", "Explainability", "Data & Exports"],
    )
    st.sidebar.markdown("### Filters")
    bands = st.sidebar.multiselect("Risk band", sorted(df["credit_score_band"].dropna().unique()))
    purposes = st.sidebar.multiselect("Loan purpose", sorted(df["loan_purpose"].dropna().unique()))
    min_pd, max_pd = st.sidebar.slider("PD range", 0.0, 1.0, (0.0, 1.0), 0.01)
    filtered = df[(df["probability_default"] >= min_pd) & (df["probability_default"] <= max_pd)]
    if bands:
        filtered = filtered[filtered["credit_score_band"].isin(bands)]
    if purposes:
        filtered = filtered[filtered["loan_purpose"].isin(purposes)]
    st.sidebar.caption(f"Showing {len(filtered):,} of {len(df):,} applications")
    return page, filtered


def render_kpis(df: pd.DataFrame, best_model: str) -> None:
    summary = portfolio_risk_summary(df)
    cols = st.columns(6)
    cols[0].metric("Applications", f"{summary['applications']:,.0f}")
    cols[1].metric("EAD", format_currency(summary["total_ead"]))
    cols[2].metric("Average PD", f"{summary['average_pd']:.2%}")
    cols[3].metric("Expected Loss", format_currency(summary["expected_loss"]))
    cols[4].metric("Default Rate", f"{summary['default_rate']:.2%}")
    cols[5].metric("Best Model", best_model)
    st.info(business_risk_narrative(summary))


def render_portfolio_page(df: pd.DataFrame, result: dict[str, object]) -> None:
    st.subheader("Portfolio Overview")
    render_kpis(df, str(result["best_model_name"]))
    tab1, tab2, tab3 = st.tabs(["Risk distribution", "Expected loss", "Delinquency"])
    with tab1:
        left, right = st.columns(2)
        left.plotly_chart(pd_distribution(df), width="stretch")
        right.plotly_chart(risk_grade_distribution(df), width="stretch")
    with tab2:
        st.plotly_chart(expected_loss_by_band(df), width="stretch")
        st.plotly_chart(px.bar(purpose_summary(df), x="loan_purpose", y="expected_loss", title="Expected Loss by Loan Purpose"), width="stretch")
        st.dataframe(risk_band_summary(df), hide_index=True, width="stretch")
    with tab3:
        st.dataframe(delinquency_analysis(df), hide_index=True, width="stretch")
        st.plotly_chart(px.bar(delinquency_analysis(df), x="delinquency_bucket", y="default_rate", title="Default Rate by Delinquency Bucket"), width="stretch")


def render_applicant_page(df: pd.DataFrame) -> None:
    st.subheader("Applicant Explorer")
    search = st.text_input("Search application ID")
    explorer = df[df["application_id"].astype(str).str.contains(search.strip(), case=False, na=False)] if search.strip() else df
    columns = [
        "application_id",
        "risk_grade",
        "credit_score_band",
        "probability_default",
        "expected_loss",
        "fico_score",
        "debt_to_income",
        "credit_utilisation",
        "loan_amount",
    ]
    st.dataframe(
        explorer[columns].sort_values("probability_default", ascending=False).head(500).style.format(
            {
                "probability_default": "{:.2%}",
                "expected_loss": "${:,.0f}",
                "debt_to_income": "{:.2%}",
                "credit_utilisation": "{:.2%}",
                "loan_amount": "${:,.0f}",
            }
        ),
        width="stretch",
        hide_index=True,
    )
    if not explorer.empty:
        selected = st.selectbox("Select applicant for explanation", explorer["application_id"].head(500))
        row = explorer[explorer["application_id"] == selected].iloc[0]
        explanation = local_customer_explanation(row)
        st.markdown(f"#### {selected}")
        st.write(explanation["explanation"])
        st.json(explanation)


def render_model_page(result: dict[str, object]) -> None:
    st.subheader("Model Performance")
    best_name = str(result["best_model_name"])
    best = result["models"][best_name]
    cols = st.columns(4)
    cols[0].metric("Best Model", best_name)
    cols[1].metric("ROC-AUC", f"{best['roc_auc']:.3f}")
    cols[2].metric("Precision", f"{best['precision']:.3f}")
    cols[3].metric("Recall", f"{best['recall']:.3f}")
    st.markdown("#### Model Benchmark")
    st.dataframe(
        result["benchmark"].style.format(
            {
                "accuracy": "{:.3f}",
                "roc_auc": "{:.3f}",
                "precision": "{:.3f}",
                "recall": "{:.3f}",
                "f1": "{:.3f}",
                "training_time": "{:.3f}s",
                "inference_time": "{:.3f}s",
            }
        ),
        hide_index=True,
        width="stretch",
    )
    tab1, tab2, tab3, tab4 = st.tabs(["Confusion Matrix", "ROC", "Precision-Recall", "Calibration & Lift"])
    with tab1:
        cm = pd.DataFrame(best["confusion_matrix"], index=["Actual non-default", "Actual default"], columns=["Predicted non-default", "Predicted default"])
        st.dataframe(cm, width="stretch")
    with tab2:
        st.plotly_chart(roc_curve_chart(best["roc_curve"]), width="stretch")
    with tab3:
        st.plotly_chart(precision_recall_chart(best["precision_recall_curve"]), width="stretch")
    with tab4:
        left, right = st.columns(2)
        left.plotly_chart(calibration_chart(best["calibration_curve"]), width="stretch")
        right.plotly_chart(lift_chart(best["lift_table"]), width="stretch")


def render_explainability_page(df: pd.DataFrame, result: dict[str, object]) -> None:
    st.subheader("Explainability")
    st.caption("The dashboard uses model feature importance and applicant-level reason codes. SHAP is used only when installed.")
    importance = global_feature_importance(result)
    st.plotly_chart(feature_importance_chart(importance), width="stretch")
    if shap_available():
        shap_frame = shap_summary_frame(result, df)
        st.dataframe(shap_frame, hide_index=True, width="stretch")
    else:
        st.warning("SHAP is not installed. Falling back to feature importance and reason codes.")
    selected = st.selectbox("Explain applicant", df["application_id"].head(500), key="explain_applicant")
    row = df[df["application_id"] == selected].iloc[0]
    st.write(local_customer_explanation(row)["explanation"])


def render_exports_page(df: pd.DataFrame, result: dict[str, object]) -> None:
    st.subheader("Data & Exports")
    status = data_source_status()
    st.json(status)
    st.download_button("Download scored predictions", df.to_csv(index=False).encode("utf-8"), "scored_credit_predictions.csv", "text/csv")
    report = pd.DataFrame([portfolio_risk_summary(df)]).to_csv(index=False).encode("utf-8")
    st.download_button("Download portfolio report", report, "portfolio_risk_summary.csv", "text/csv")
    st.dataframe(df.head(100), width="stretch")


def main() -> None:
    st.title("Credit Risk Analytics Platform")
    st.caption("Enterprise-style credit risk analytics for PD modelling, expected loss and explainability.")
    result = get_model_result()
    df = result["scored_data"].copy()
    page, filtered = render_sidebar(df)

    if page == "Portfolio Overview":
        render_portfolio_page(filtered, result)
    elif page == "Applicant Explorer":
        render_applicant_page(filtered)
    elif page == "Model Performance":
        render_model_page(result)
    elif page == "Explainability":
        render_explainability_page(filtered, result)
    elif page == "Data & Exports":
        render_exports_page(filtered, result)


if __name__ == "__main__":
    main()

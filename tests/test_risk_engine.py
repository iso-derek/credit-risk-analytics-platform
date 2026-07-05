import pandas as pd

from src.risk_engine import business_risk_narrative, enrich_risk_metrics, portfolio_risk_summary, risk_grade


def test_risk_grade_maps_pd_to_ordered_grade() -> None:
    assert risk_grade(0.02).startswith("Grade 1")
    assert risk_grade(0.40).startswith("Grade 6")


def test_enrich_risk_metrics_adds_expected_loss_fields() -> None:
    df = pd.DataFrame(
        {
            "application_id": ["A1"],
            "probability_default": [0.1],
            "credit_score_band": ["C - Moderate Risk"],
            "loan_amount": [10000],
            "num_delinquencies": [1],
            "credit_utilisation": [0.7],
            "default": [0],
        }
    )
    enriched = enrich_risk_metrics(df, lgd=0.5)
    assert enriched.loc[0, "expected_loss"] == 500
    assert enriched.loc[0, "risk_grade"]


def test_portfolio_risk_summary_and_narrative() -> None:
    df = pd.DataFrame({"ead": [1000, 2000], "expected_loss": [50, 100], "pd": [0.05, 0.1], "default": [0, 1], "num_delinquencies": [0, 2]})
    summary = portfolio_risk_summary(df)
    assert summary["total_ead"] == 3000
    assert "portfolio contains" in business_risk_narrative(summary).lower()

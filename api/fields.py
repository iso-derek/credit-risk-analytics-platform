"""Plain-English names and display types for every field the app shows.

The web app never shows raw column names: each field is described here with a
label, a display ``kind`` (how the value should be formatted) and, where useful,
a one-line explanation a non-specialist can follow.
"""
from __future__ import annotations

import re

# kind: money | percent | integer | number | years | months | score | text | flag
FIELDS: dict[str, dict[str, str]] = {
    "application_id": {"label": "Application", "kind": "text"},
    "age": {"label": "Age", "kind": "years", "help": "Applicant age in years."},
    "annual_income": {"label": "Annual income", "kind": "money"},
    "loan_amount": {"label": "Loan amount", "kind": "money"},
    "loan_term_months": {"label": "Loan term", "kind": "months"},
    "interest_rate": {"label": "Interest rate", "kind": "percent"},
    "debt_to_income": {"label": "Debt-to-income ratio", "kind": "percent",
                       "help": "Monthly debt payments as a share of income."},
    "fico_score": {"label": "Credit score (FICO)", "kind": "score", "help": "Higher is better; 300–850."},
    "credit_history_years": {"label": "Credit history", "kind": "years"},
    "credit_utilisation": {"label": "Credit utilisation", "kind": "percent",
                           "help": "Share of available credit currently used."},
    "num_delinquencies": {"label": "Missed-payment records", "kind": "integer"},
    "recent_inquiries": {"label": "Recent credit applications", "kind": "integer"},
    "open_accounts": {"label": "Open accounts", "kind": "integer"},
    "employment_status": {"label": "Employment", "kind": "text"},
    "home_ownership": {"label": "Home ownership", "kind": "text"},
    "loan_purpose": {"label": "Loan purpose", "kind": "text"},
    "loan_to_income": {"label": "Loan-to-income ratio", "kind": "percent"},
    "high_dti_flag": {"label": "High debt-to-income", "kind": "flag"},
    "high_utilisation_flag": {"label": "High utilisation", "kind": "flag"},
    "thin_file_flag": {"label": "Short credit history", "kind": "flag"},
    "recent_credit_seeking_flag": {"label": "Seeking a lot of new credit", "kind": "flag"},
    "subprime_flag": {"label": "Subprime credit score", "kind": "flag"},
    "risk_rule_score": {"label": "Rule-based warning count", "kind": "integer"},
    "credit_score_band": {"label": "Risk band", "kind": "text"},
    "age_band": {"label": "Age group", "kind": "text"},
    # UCI public credit-card benchmark (amounts in New Taiwan dollars).
    "LIMIT_BAL": {"label": "Credit limit", "kind": "money"},
    "SEX": {"label": "Sex (dataset code)", "kind": "text"},
    "EDUCATION": {"label": "Education (dataset code)", "kind": "text"},
    "MARRIAGE": {"label": "Marital status (dataset code)", "kind": "text"},
    "AGE": {"label": "Age", "kind": "years"},
    "exposure_proxy": {"label": "Exposure", "kind": "money"},
    # Statlog German Credit (amounts in Deutsche Mark).
    "checking_account": {"label": "Checking account balance", "kind": "text"},
    "duration_months": {"label": "Loan length", "kind": "months"},
    "credit_history": {"label": "Credit history", "kind": "text"},
    "purpose": {"label": "Loan purpose", "kind": "text"},
    "credit_amount": {"label": "Credit amount", "kind": "money"},
    "savings": {"label": "Savings", "kind": "text"},
    "employment_since": {"label": "Time in current job", "kind": "text"},
    "installment_rate": {"label": "Repayments as share of income (1–4 scale)", "kind": "integer",
                         "help": "1 = lowest burden, 4 = highest."},
    "other_debtors": {"label": "Co-applicant or guarantor", "kind": "text"},
    "residence_years": {"label": "Years at current address (1–4 scale)", "kind": "integer"},
    "property": {"label": "Most valuable property", "kind": "text"},
    "other_installment_plans": {"label": "Other repayment plans", "kind": "text"},
    "housing": {"label": "Housing", "kind": "text"},
    "existing_credits": {"label": "Existing loans at this bank", "kind": "integer"},
    "job": {"label": "Job", "kind": "text"},
    "dependants": {"label": "People financially dependent", "kind": "integer"},
    "telephone": {"label": "Registered telephone", "kind": "text"},
    "foreign_worker": {"label": "Foreign worker", "kind": "text"},
    "sex": {"label": "Sex", "kind": "text"},
}
_MONTHS = ["September", "August", "July", "June", "May", "April"]
for _i, _month in enumerate(_MONTHS, start=1):
    FIELDS[f"BILL_AMT{_i}"] = {"label": f"{_month} statement balance", "kind": "money"}
    FIELDS[f"PAY_AMT{_i}"] = {"label": f"{_month} payment", "kind": "money"}
for _code, _month in zip(["PAY_0", "PAY_2", "PAY_3", "PAY_4", "PAY_5", "PAY_6"], _MONTHS):
    FIELDS[_code] = {"label": f"{_month} repayment status", "kind": "repayment",
                     "help": "Paid on time, or how many months the payment was late."}

ACRONYMS = {"id": "ID", "pd": "PD", "usd": "USD", "fico": "FICO"}


def label(name: str) -> str:
    """Readable label for any field, falling back to a cleaned-up name."""
    if name in FIELDS:
        return FIELDS[name]["label"]
    words = [ACRONYMS.get(word.lower(), word) for word in re.split(r"[_\s]+", str(name)) if word]
    text = " ".join(words)
    return text[:1].upper() + text[1:].lower() if text.isupper() else text[:1].upper() + text[1:]


def kind(name: str) -> str:
    return FIELDS.get(name, {}).get("kind", "text")


def describe(name: str) -> dict[str, str]:
    entry = {"key": name, "label": label(name), "kind": kind(name)}
    if help_text := FIELDS.get(name, {}).get("help"):
        entry["help"] = help_text
    return entry

# Credit Risk Analytics Platform

An enterprise-style Python credit risk analytics platform for probability of default modelling, portfolio risk monitoring, expected loss analysis and business-friendly applicant explanations.

This project is designed as a finance, risk analytics and data science portfolio project. It demonstrates how a lending analytics workflow can move from raw application data to feature engineering, model training, PD scoring, risk banding, expected loss analysis and dashboard reporting.

> Educational use only. This project is not a production lending decision engine and should not be used to approve or reject real credit applications.

## Business Problem

Banks, fintech lenders and credit teams need to evaluate borrower risk consistently while keeping model outputs explainable to risk, operations and business stakeholders. A useful credit risk system needs to answer:

- Which applicants are most likely to default?
- Which segments concentrate expected loss?
- Which credit drivers explain elevated risk?
- How well does the model separate good and bad applicants?
- How should portfolio risk be monitored over time?

This platform addresses those questions with a complete analytical workflow for credit application scoring and portfolio review.

## Financial Context

The project uses common retail credit risk concepts:

- **Probability of Default (PD):** estimated likelihood that an applicant defaults.
- **Loss Given Default (LGD):** share of exposure lost if default occurs.
- **Exposure at Default (EAD):** expected outstanding balance at default.
- **Expected Loss (EL):** `PD x LGD x EAD`.
- **Risk Grades:** business-friendly bands derived from PD.
- **Portfolio Risk:** aggregate exposure, expected loss, observed default rate and concentration by segment.

## Machine Learning Pipeline

1. Load credit application data from a configured local dataset path.
2. Fall back to synthetic credit data when no external dataset is available.
3. Validate required fields, identify duplicates and handle missing values.
4. Engineer credit risk features such as loan-to-income, utilisation flags, thin-file flags and risk rule scores.
5. Train benchmark classification models.
6. Evaluate model performance using classification and ranking metrics.
7. Score applications with probability of default.
8. Convert PD into risk bands and expected loss.
9. Display portfolio analytics, model performance and applicant-level explanations in Streamlit.

## Project Architecture

```text
credit-risk-analytics-platform/
  app.py
  requirements.txt
  README.md
  CHANGELOG.md
  ROADMAP.md
  CONTRIBUTING.md
  data/
    raw/
    processed/
  src/
    analytics.py
    data_generation.py
    modelling.py
    preprocessing.py
    visualisation.py
  notebooks/
  outputs/
  screenshots/
  assets/
```

## Dataset

Version 1.0 uses a realistic synthetic loan application dataset generated locally. The dataset includes:

- Applicant income and age
- Loan amount, interest rate and term
- FICO score
- Debt-to-income ratio
- Credit utilisation
- Credit history length
- Recent inquiries
- Delinquencies
- Employment status
- Home ownership
- Loan purpose
- Default outcome

Phase 2 adds configurable support for public credit datasets while keeping synthetic data as a fallback for reproducibility.

### External Dataset Configuration

Place a public credit dataset with the expected schema at:

```text
data/raw/public_credit_dataset.csv
```

Or set a custom path:

```bash
set CREDIT_DATA_PATH=C:\path\to\public_credit_dataset.csv
```

On macOS or Linux:

```bash
export CREDIT_DATA_PATH=/path/to/public_credit_dataset.csv
```

If the external dataset is missing or does not include the required fields, the project falls back to synthetic demo data.

## Risk Modelling Methodology

The baseline modelling workflow trains multiple classification models using engineered borrower and loan features. The best model is selected by ROC-AUC and used to produce PD estimates. PD values are translated into credit risk bands and expected loss is calculated using a configurable LGD assumption.

Core modelling components:

- Missing value imputation
- Categorical one-hot encoding
- Numeric scaling
- Logistic Regression
- Random Forest
- Optional gradient-boosted models when installed
- Model comparison by ranking and classification metrics
- Feature importance-based explanation

## Evaluation Metrics

The platform reports:

- ROC-AUC
- Precision
- Recall
- Confusion matrix
- Expected loss
- Observed default rate
- Average PD
- Portfolio exposure
- Risk-band distribution

Phase 2 expands this with calibration, lift, precision-recall and model benchmarking views.

## Dashboard Overview

The Streamlit dashboard includes:

- Portfolio risk summary
- PD distribution
- Expected loss by credit score band
- Expected loss by loan purpose
- Applicant explorer
- Model explanation
- Data preview

## Installation

Use Python 3.11 or newer.

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

On macOS or Linux:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run Locally

```bash
python src/data_generation.py
python src/modelling.py
streamlit run app.py
```

## Screenshots

Add screenshots after running the dashboard:

```text
screenshots/portfolio-overview.png
screenshots/risk-distribution.png
screenshots/applicant-explorer.png
screenshots/model-performance.png
screenshots/explainability.png
```

## Results

The platform demonstrates how a credit risk team could combine machine learning predictions with business risk metrics. It links applicant-level PD estimates to portfolio expected loss, score bands and explainable risk drivers.

## Limitations

- Synthetic data is useful for demonstration but does not replace real model validation.
- The current model is not calibrated for production lending.
- No reject inference, macroeconomic stress testing or fairness review is included yet.
- Explanations are educational and should be reviewed by qualified risk stakeholders.

## Roadmap

See [ROADMAP.md](ROADMAP.md).

## Changelog

See [CHANGELOG.md](CHANGELOG.md).

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## Author

Derek Ohimai Isokpehi  
GitHub: [iso-derek](https://github.com/iso-derek)

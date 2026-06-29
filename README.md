# Credit Risk Analytics Platform

## Overview

Credit Risk Analytics Platform is a Python data science project for loan default prediction, probability of default modelling, credit score banding, and expected loss analysis. It uses a realistic synthetic loan dataset and includes a Streamlit dashboard for portfolio and applicant-level risk review.

The project is suitable for MSc Finance & Data Science / Financial Engineering applications, graduate risk analytics roles, fintech roles, consulting analytics roles, and data science portfolios.

This project is for educational and analytical purposes only. It is not a production lending decision engine.

## Business Problem

Lenders and fintech teams need to evaluate applicant risk, estimate probability of default, monitor portfolio exposure, and explain the main drivers of credit risk. This project demonstrates how a credit analytics workflow can move from raw applications to model scoring, risk bands, expected loss, and dashboard reporting.

## Key Features

- Synthetic loan application dataset
- Missing value and categorical preprocessing
- Feature engineering for credit risk
- Logistic Regression model
- Random Forest model
- Optional XGBoost model if installed
- Probability of Default scoring
- Credit score bands
- Expected loss calculation using PD, LGD, and EAD
- ROC-AUC, precision, recall, and confusion matrix
- Feature importance explanation
- Streamlit dashboard for applicant and portfolio risk

## Technologies Used

- Python
- pandas
- NumPy
- scikit-learn
- Streamlit
- Plotly
- Optional XGBoost

## Project Structure

```text
credit-risk-analytics-platform/
  README.md
  requirements.txt
  .gitignore
  app.py
  data/
    raw/
    processed/
  src/
    data_generation.py
    preprocessing.py
    modelling.py
    analytics.py
    visualisation.py
  notebooks/
  outputs/
  screenshots/
  assets/
```

## Methodology

1. Generate a synthetic loan portfolio with realistic applicant risk drivers.
2. Engineer features such as loan-to-income, high utilisation flag, thin file flag, and risk rule score.
3. Train multiple classification models.
4. Select the best model by ROC-AUC.
5. Score applications with probability of default.
6. Convert PD values into credit risk bands.
7. Estimate expected loss using PD, LGD, and EAD.
8. Present portfolio risk and model explanation in Streamlit.

## How To Run

```bash
pip install -r requirements.txt
python src/data_generation.py
python src/modelling.py
streamlit run app.py
```

## Dashboard Screenshots

Add screenshots to the `screenshots/` folder after running the app locally.

Suggested screenshots:

- Portfolio risk summary
- PD distribution
- Expected loss by score band
- Applicant explorer
- Feature importance

## Results / Insights

The platform helps answer:

- Which applicants are most likely to default?
- Which score bands concentrate expected loss?
- How does debt-to-income affect credit risk?
- Which loan purposes contribute most expected loss?
- Which features are most influential in the model?

## Skills Demonstrated

- Credit risk modelling
- Probability of default estimation
- Expected loss analytics
- Model evaluation
- Feature engineering
- Classification pipelines
- Streamlit dashboard development

## Future Improvements

- SHAP explainability
- Real public credit dataset option
- Calibration curves
- Reject inference discussion
- IFRS 9 staging logic
- Macroeconomic stress testing
- Model monitoring and drift checks

## Author

Derek Ohimai Isokpehi  
GitHub: [iso-derek](https://github.com/iso-derek)

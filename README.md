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
- Probability of Default scoring
- Credit score bands
- Expected loss calculation using PD, LGD, and EAD
- ROC-AUC, average precision, Brier score, log loss and reliability plots
- Feature importance explanation
- Streamlit dashboard for applicant and portfolio risk

## Technologies Used

- Python
- pandas
- NumPy
- scikit-learn
- Streamlit
- Plotly

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
4. Select a probability model by validation log loss and a ranking comparator by validation ROC-AUC; freeze both before final testing.
5. Score applications with probability of default.
6. Convert PD values into credit risk bands.
7. Estimate expected loss using PD, LGD, and EAD.
8. Present portfolio risk and model explanation in Streamlit.

## How To Run

```bash
pip install -r requirements.txt
python src/data_generation.py
python scripts/run_research.py
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
- Reject inference discussion
- IFRS 9 staging logic
- Macroeconomic stress testing
- Model monitoring and drift checks

## Author

Derek Ohimai Isokpehi  
GitHub: [iso-derek](https://github.com/iso-derek)

## Research upgrade

Run `streamlit run app.py` for portfolio review, reliability plots, model sensitivity,
loss scenarios and downloadable experiment bundles. The public benchmark can be
selected in the sidebar. No silent fallback is used if its download fails.

- Four disjoint applicant partitions: training (55%), calibration (15%), selection
  (15%) and final test (15%). Only held-out applicants populate portfolio metrics.
- Logistic regression and random forest, each raw and sigmoid-calibrated. Natural
  class proportions are preserved. The winner is chosen by validation log loss.
- ROC-AUC, average precision, Brier score, log loss, reliability plots and a paired
  applicant-bootstrap comparison against the validation AUC winner.
- Expected loss sensitivity to assumed default odds, LGD and exposure; these are
  scenarios, not estimated macroeconomic responses or realised recovery losses.
- Applicant sensitivity uses changes in the actual fitted model. It is explicitly
  distinguished from causal attribution. Permutation importance uses validation data.

```bash
python -m unittest discover -s tests -v
python scripts/run_research.py --dataset synthetic
python scripts/run_research.py --dataset uci --output outputs/uci_study.zip
```

See [research protocol](docs/RESEARCH_PROTOCOL.md) and [recorded run](docs/RESEARCH_RESULTS.md).
The public adapter preserves Taiwan-dollar units and uses statement balance as an
exposure proxy; it does not invent income or FICO values. Raw public data is fetched
from UCI on request, not redistributed here.
# One-command local launch

On Windows with Python 3.13, double-click `Start.cmd`, or run `py -3.13 launch.py` in this folder. Python 3.12 is also supported. See [quick start and research history](docs/QUICKSTART.md).

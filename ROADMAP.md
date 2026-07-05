# Roadmap

## Version 2.0

### Professional Documentation

- Maintain a clear README for recruiters and technical reviewers.
- Add screenshots for each dashboard page.
- Keep the changelog updated by feature branch.

### Data Pipeline

- Support configured external public credit datasets.
- Keep synthetic fallback data for reproducibility.
- Validate schemas and surface data quality warnings.
- Add missing value, duplicate and feature quality checks.

### Risk Engine

- Add professional credit risk metrics: PD, LGD, EAD, expected loss, risk grades and risk bands.
- Add delinquency analysis, lift charts, calibration curves and model performance charts.
- Add business-friendly explanations for portfolio risk.

### Explainability

- Add optional SHAP explanations when installed.
- Add global feature importance and local applicant reason codes.
- Add natural-language risk reasons for individual applicants.

### Dashboard

- Add sidebar navigation and dedicated pages.
- Add KPI cards, customer search, model performance and explainability pages.
- Add exportable predictions and portfolio reports.

### Engineering

- Add logging and configuration.
- Add unit and integration tests.
- Add pre-commit hooks and GitHub Actions CI.
- Add Docker support and deployment documentation.

## Future Ideas

- Macroeconomic stress testing.
- IFRS 9 staging logic.
- Fairness and bias diagnostics.
- Model monitoring and drift detection.
- Reject inference discussion.
- Scorecard-style model documentation.

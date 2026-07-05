# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Planned

### Added

- Added configurable external public credit dataset path support.
- Added data quality validation for required columns, duplicates and missing values.
- Added synthetic fallback data handling when external data is unavailable.
- Added credit risk engine metrics for PD, LGD, EAD, expected loss, risk grades and delinquency analysis.
- Added ROC, precision-recall, calibration and lift table outputs for model evaluation.
- Added explainable AI helpers with optional SHAP support.
- Added local applicant reason codes and natural-language risk explanations.
- Upgraded Streamlit dashboard with sidebar navigation, KPI cards, customer search, performance pages, explainability pages and export buttons.
- Added Gradient Boosting and optional LightGBM model support.
- Added model benchmark table with accuracy, ROC-AUC, precision, recall, F1, training time and inference time.
- Added unit tests, CI workflow, pre-commit configuration, Dockerfile, `.dockerignore` and `.env.example`.
- Added basic logging configuration for model training.

## [1.0.0] - 2026-06-26

### Added

- Synthetic loan application dataset generator.
- Credit risk feature engineering pipeline.
- Logistic Regression and Random Forest model training.
- Probability of default scoring.
- Credit score banding.
- Expected loss calculation using PD, LGD and EAD.
- Streamlit dashboard for portfolio and applicant review.
- Feature importance view for model interpretation.

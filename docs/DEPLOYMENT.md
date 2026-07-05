# Deployment Guide

This guide describes how to deploy the Credit Risk Analytics Platform for portfolio review.

## Deployment Checklist

- Confirm the data is synthetic, public or approved for sharing.
- Run `pytest`.
- Run `python src/modelling.py`.
- Run `streamlit run app.py`.
- Confirm the dashboard loads without exceptions.
- Add screenshots to the `screenshots/` folder.

## Streamlit Cloud

1. Push the repository to GitHub.
2. Go to Streamlit Community Cloud.
3. Create a new app from the repository.
4. Set the app entry point to:

```text
app.py
```

5. Add any environment variables if needed:

```text
CREDIT_DATA_PATH=data/raw/public_credit_dataset.csv
CREDIT_LGD=0.45
```

If no external dataset is provided, the app uses synthetic fallback data.

## Render

Use the following settings:

- Environment: Python
- Build command: `pip install -r requirements.txt`
- Start command: `streamlit run app.py --server.address 0.0.0.0 --server.port $PORT`

Environment variables:

```text
CREDIT_LGD=0.45
```

## Docker

Build:

```bash
docker build -t credit-risk-analytics-platform .
```

Run:

```bash
docker run --rm -p 8501:8501 credit-risk-analytics-platform
```

Open:

```text
http://localhost:8501
```

## Health Checks

For a running Streamlit service, use:

```text
/_stcore/health
```

Example:

```text
http://localhost:8501/_stcore/health
```

## Data Security

Do not deploy private applicant data or personally identifiable information. Use synthetic, anonymised or public datasets only.

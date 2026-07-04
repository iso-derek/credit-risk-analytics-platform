# Contributing

This project uses a branch-based workflow.

## Workflow

1. Open or select a GitHub issue.
2. Create a dedicated branch from the current review base.
3. Make small, focused commits.
4. Run validation before pushing.
5. Open a pull request.
6. Do not merge directly into `main`.

## Local Checks

```bash
python src/data_generation.py
python src/modelling.py
streamlit run app.py
```

When tests are added:

```bash
pytest
```

## Code Style

- Keep functions small and business-readable.
- Prefer typed helper functions for reusable analytics.
- Keep dashboard code focused on presentation and move calculations into `src/`.
- Avoid committing private datasets, API keys or personally identifiable information.

## Data Policy

Only use public, synthetic or approved datasets. Any real credit data must be anonymised and legally shareable before it is committed to the repository.

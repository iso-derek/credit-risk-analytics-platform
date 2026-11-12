# Monitoring operating runbook

This runbook defines a deployable monitoring contract without claiming that the
current same-cohort dashboard is live production monitoring.

## Required cohort

Each immutable scoring cohort must contain a unique `application_id`, an ISO-8601
`observed_at` timestamp, and every model input used at scoring time. The cohort must
be cut with an explicit UTC `as_of` timestamp. Future-dated rows, duplicate IDs,
invalid timestamps, missing required fields, and cohorts below the configured minimum
are rejected.

Validate a CSV before computing monitoring evidence:

```bash
python scripts/validate_monitoring_cohort.py cohort.csv --features income loan_amount credit_score --as-of 2026-11-01T00:00:00Z
```

## Delayed outcomes

Performance and calibration review must use only rows old enough to satisfy the
configured outcome lag. The validator reports eligible rows, immature rows, missing
eligible labels, and eligible-label coverage. Immature rows can support input and
score drift review but cannot support outcome-performance conclusions.

## Ownership and response

The machine-readable policy is `config/monitoring_policy.json`.

- Model Risk Owner reviews feature and score PSI, business mix, calibration and
  discrimination once outcomes mature.
- Data Quality Owner investigates missingness, schema and upstream completeness.
- Platform Engineering Owner owns job execution, evidence persistence and failures.
- No signal automatically blocks decisions, retrains, recalibrates or replaces a
  model. Every material signal requires a documented human disposition.

For a high signal, record the cohort identifier, cutoff, policy version, evidence,
probable cause, impact assessment, owner, decision and follow-up date. A moderate
signal is reviewed with volume, portfolio mix and data-quality context. A clean run
is retained as evidence rather than discarded.

## Evidence and release boundary

Retain the cohort manifest, policy version, drift tables, score summary, alert
register, outcome-maturity summary, dependency inventory and code commit. The policy
sets a 24-month evidence target, subject to an approved privacy and retention review.

This repository does not schedule a live job, ingest private applications, or name
individual operating owners. Those require an approved host, access controls, named
accountability and a data-retention decision.

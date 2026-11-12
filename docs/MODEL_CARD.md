# Model card — credit risk research demonstration

## Intended use

This project demonstrates leakage-resistant probability modelling, held-out evidence,
portfolio loss sensitivity, subgroup diagnostics and monitoring controls. It supports
education, portfolio review and research workflow discussion. It is not approved for
automated credit decisions, adverse-action reasons, pricing, regulatory compliance or
production lending.

## Data and target

The default mode uses locally generated synthetic applications. The optional public
benchmark is the UCI Default of Credit Card Clients cohort from Taiwan in 2005, with
next-month default as its outcome. It is a single historical cohort and does not
establish current, geographic or product transfer. Statement balance is used as an
exposure proxy and LGD is assumed, so expected loss is illustrative rather than an
observed recovery estimate.

## Model development

Applicants are divided into disjoint training, calibration, validation-selection and
final-test partitions. Model choice uses validation evidence; the final test is used
only after selection. The dashboard reports discrimination, probability loss,
reliability, sensitivity and portfolio summaries. Reproducible bundles retain split,
prediction, metric, drift and provenance evidence.

## Subgroups and monitoring

Subgroup results are conditional diagnostics with minimum-size and two-outcome
suppression. They are not causal or legal fairness findings. Same-cohort PSI is a
development signal, not temporal monitoring. The operational contract separately
requires timestamped immutable cohorts, delayed-outcome maturity, named ownership and
human disposition; no signal automatically changes a model.

## Material limitations

- No external or genuinely out-of-time validation has been accepted.
- Synthetic realism does not establish real borrower or portfolio performance.
- The public benchmark is historical and context-specific.
- Imputation, correlated predictors and replacement sensitivity limit explanation.
- Assumed LGD and exposure proxies do not validate realised loss.
- No authentication, private-data workflow or hosted operating owner is approved.

## Release governance

`config/release_gate.json` separates completed repository evidence from approvals and
evidence that cannot be manufactured in code. Run `python scripts/release_readiness.py`
to print the current report. A non-zero exit while blockers remain is expected and
prevents technical polish from being misrepresented as stable-release approval.

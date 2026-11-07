# Portfolio diagnostics

The Portfolio tab describes data coverage and concentration in the untouched
final-test cohort. These views do not refit the model or influence model selection.

## Held-out data coverage

Missing counts and rates are calculated on retained raw predictor fields before the
fitted preprocessing pipeline applies median or most-frequent-value imputation.
This makes imputation dependence visible instead of presenting model-ready values as
complete source data. Zero missingness does not prove accuracy, freshness or
representativeness.

## Segment exposure and expected loss

Supported segment views reconcile applicant count, exposure and expected loss to the
held-out portfolio totals. Each view reports mean predicted PD, observed default rate,
and applicant, exposure and expected-loss shares.

The concentration cards show the largest segment shares and a Herfindahl-Hirschman
Index (HHI), calculated as the sum of squared segment shares. Values near zero are
more diffuse and one means a single segment holds the entire amount. The dashboard
does not assign a risk appetite limit or regulatory interpretation.

Expected loss remains conditional on the displayed exposure proxy and assumed 45%
LGD. It is not realised loss, an accounting impairment estimate or a forecast.

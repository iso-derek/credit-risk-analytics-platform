# Probability quality versus ranking in credit risk

Question: does selecting a model for probability quality improve held-out loss
proxies compared with selecting for ranking quality?

## Frozen experiment
Use a fixed seed and distinct applicants across training, sigmoid calibration,
validation and final evaluation. Fit preprocessing only on training. Choose a
probability model by validation log loss and a ranking model by validation ROC-AUC.
Do not retune models from final-test results. Compare all candidates transparently.
The selections may coincide; this is an admissible null comparison.

Evaluate ROC-AUC, average precision, Brier score, log loss and reliability diagrams.
A 95% percentile bootstrap interval for the paired difference in Brier losses uses
1,000 applicant resamples. This conditions on fitted models and assumes independent
applicants; it does not incorporate retraining or temporal dependence uncertainty.

## Financial assumptions
Expected loss = PD × assumed LGD × exposure proxy. The synthetic example uses loan
amounts and USD. The public dataset uses Taiwan dollars and non-negative latest
statement balance. Credit limits are not silently substituted for observed EAD.
Default-weighted loss proxies use the same assumed LGD and are not realised losses.
Odds stress changes p to m*p/(1-p+m*p), preserving [0,1]. LGD and exposure multipliers
are explicit scenario assumptions, not inferred effects of a recession.

## Data and interpretation
Public source: Yeh, I. (2009), Default of Credit Card Clients, UCI, DOI
https://doi.org/10.24432/C55S3H (CC BY 4.0).
https://archive.ics.uci.edu/dataset/350/defaultofcreditcardclients
The outcome is next-month default for a 2005 Taiwan cohort. Stratified applicant
holdouts do not establish performance over later years or other countries.
Only financial features enter the public benchmark; excluding demographics does not
establish fairness. The platform is an educational research tool, not a lending engine.

References for implementation:
https://scikit-learn.org/stable/modules/calibration.html
https://scikit-learn.org/stable/modules/cross_validation.html

## Reproduction
Use scripts/run_research.py. Exported settings include seed, dataset/source hashes,
selection rule, assumptions, input schema, predictions and split membership.
Record future studies separately; do not overwrite the protocol to fit test outcomes.
A literature review and independent data are required before claiming novelty.

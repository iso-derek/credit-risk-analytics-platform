# Recorded public-data experiment

Dataset: UCI Default of Credit Card Clients, 30,000 applicants; 4,500 held out.
Seed: 42. This is one fixed, exploratory cohort experiment.

| Candidate | ROC-AUC | Brier | Log loss | Loss-proxy error (TWD) |
|---|---:|---:|---:|---:|
| Logistic regression / raw | 0.7584 | 0.1383 | 0.4417 | -891,375 |
| Logistic regression / calibrated | 0.7584 | 0.1382 | 0.4413 | -904,212 |
| Random forest / raw | 0.7769 | 0.1365 | 0.4346 | -1,220,470 |
| Random forest / calibrated | 0.7769 | 0.1358 | 0.4323 | -1,404,585 |

Validation log-loss choice: **Random forest / calibrated**.
Validation ranking choice: **Random forest / raw**.
Paired test Brier difference: -0.000689; percentile 95% interval [-0.001349, -0.000017].

The calibrated forest had a larger absolute aggregate loss-proxy error than the raw forest in this test. Better unweighted probability scores did not translate into a better currency-weighted loss estimate.

This run shows a small conditional improvement in Brier loss for the calibrated selection. It does not establish general superiority, performance through time, or accurate recovery-loss estimates. Both comparison choices and every parameter were fixed before the final test was evaluated.

Loss-proxy error compares expected loss against default × assumed 45% LGD × statement-balance proxy. Actual recoveries are unavailable.

Input SHA-256: `174704744c1371dc2773fe0b1db92fed42a84d7e1c6ae4f7a84896e01f2647fd`

Reproduce with `python scripts/run_research.py --dataset uci`. Downloadable bundles include all test predictions, partition membership and settings.

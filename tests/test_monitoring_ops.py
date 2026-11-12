import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import unittest
import pandas as pd

from monitoring_ops import (
    load_monitoring_policy, outcome_maturity_summary, route_monitoring_signals,
    validate_timestamped_cohort,
)


class MonitoringOperationsTests(unittest.TestCase):
    def setUp(self):
        self.cohort = pd.DataFrame({
            "application_id": [1, 2, 3],
            "observed_at": ["2026-01-01T00:00:00Z", "2026-01-15T00:00:00Z", "2026-03-15T00:00:00Z"],
            "income": [10, 20, 30],
            "default": [0, 1, None],
        })

    def test_policy_is_complete_and_disables_automatic_action(self):
        policy = load_monitoring_policy()
        self.assertFalse(policy["automatic_model_action"])
        self.assertEqual(policy["owners"]["model_risk"], "Model Risk Owner")

    def test_timestamped_cohort_manifest(self):
        result = validate_timestamped_cohort(
            self.cohort, ["income"], as_of="2026-04-01T00:00:00Z", minimum_rows=3,
        )
        self.assertEqual(result["row_count"], 3)
        self.assertEqual(result["cohort_start_utc"], "2026-01-01T00:00:00+00:00")

    def test_cohort_rejects_duplicate_ids_future_rows_and_missing_features(self):
        duplicate = self.cohort.copy(); duplicate.loc[1, "application_id"] = 1
        with self.assertRaisesRegex(ValueError, "unique"):
            validate_timestamped_cohort(duplicate, ["income"], as_of="2026-04-01")
        with self.assertRaisesRegex(ValueError, "after"):
            validate_timestamped_cohort(self.cohort, ["income"], as_of="2026-02-01")
        with self.assertRaisesRegex(ValueError, "missing"):
            validate_timestamped_cohort(self.cohort, ["unknown"], as_of="2026-04-01")

    def test_outcome_maturity_separates_eligible_and_immature_rows(self):
        result = outcome_maturity_summary(self.cohort, as_of="2026-04-01", outcome_lag_days=60)
        self.assertEqual(result["eligible_rows"], 2)
        self.assertEqual(result["immature_rows"], 1)
        self.assertEqual(result["eligible_label_coverage"], 1.0)

    def test_alerts_are_owned_and_do_not_imply_automatic_action(self):
        policy = load_monitoring_policy()
        drift = pd.DataFrame({
            "feature": ["income", "purpose"], "psi": [.30, .12],
            "missing_rate_change": [.01, .08],
        })
        alerts = route_monitoring_signals(drift, {"psi": .11}, policy)
        self.assertEqual(len(alerts), 4)
        self.assertIn("Data Quality Owner", alerts.owner.tolist())
        self.assertTrue(alerts.required_action.str.contains("Review|Investigate|Trace").all())

    def test_no_signal_returns_a_stable_empty_schema(self):
        policy = load_monitoring_policy()
        drift = pd.DataFrame({"feature": ["income"], "psi": [.01], "missing_rate_change": [.01]})
        alerts = route_monitoring_signals(drift, {"psi": .02}, policy)
        self.assertTrue(alerts.empty)
        self.assertEqual(alerts.columns.tolist(), ["signal", "value", "severity", "owner", "required_action"])


if __name__ == "__main__":
    unittest.main()

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import unittest
import numpy as np
import pandas as pd

from analytics import concentration_summary, missingness_summary, segment_loss_summary


class PortfolioDiagnosticTests(unittest.TestCase):
    def setUp(self):
        self.frame = pd.DataFrame({
            "application_id": ["A", "B", "C", "D"],
            "segment": ["Retail", "Retail", "Business", None],
            "feature": [1.0, np.nan, 3.0, np.nan],
            "probability_default": [.1, .2, .3, .4],
            "default": [0, 0, 1, 1],
            "ead": [100.0, 200.0, 300.0, 400.0],
            "expected_loss": [4.5, 18.0, 40.5, 72.0],
        })

    def test_missingness_reports_raw_holdout_coverage(self):
        result = missingness_summary(self.frame, ["feature", "segment"])
        feature = result.set_index("field").loc["feature"]
        self.assertEqual(feature.missing_applicants, 2)
        self.assertEqual(feature.missing_rate, .5)
        self.assertIn("imputes", feature.coverage_status)

    def test_segment_totals_and_shares_reconcile(self):
        result = segment_loss_summary(self.frame, "segment")
        self.assertEqual(set(result.segment), {"Retail", "Business", "Missing"})
        self.assertAlmostEqual(result.total_exposure.sum(), self.frame.ead.sum())
        self.assertAlmostEqual(result.expected_loss.sum(), self.frame.expected_loss.sum())
        self.assertAlmostEqual(result.exposure_share.sum(), 1.0)
        self.assertAlmostEqual(result.expected_loss_share.sum(), 1.0)
        retail = result.set_index("segment").loc["Retail"]
        self.assertEqual(retail.applicants, 2)
        self.assertAlmostEqual(retail.mean_predicted_pd, .15)

    def test_concentration_is_descriptive_and_bounded(self):
        result = concentration_summary(segment_loss_summary(self.frame, "segment"))
        self.assertEqual(result["segments"], 3)
        self.assertTrue(0 < result["exposure_hhi"] <= 1)
        self.assertTrue(0 < result["expected_loss_hhi"] <= 1)

    def test_invalid_inputs_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "Missing portfolio fields"):
            missingness_summary(self.frame, ["unknown"])
        with self.assertRaisesRegex(ValueError, "Missing segment fields"):
            segment_loss_summary(self.frame, "unknown")
        with self.assertRaises(ValueError):
            concentration_summary(pd.DataFrame())


if __name__ == "__main__":
    unittest.main()

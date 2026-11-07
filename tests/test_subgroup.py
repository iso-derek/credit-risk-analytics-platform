import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import unittest
import numpy as np
import pandas as pd

from subgroup import add_audit_groups, add_intersection_group, available_group_columns, subgroup_diagnostics


class SubgroupTests(unittest.TestCase):
    def setUp(self):
        self.frame = pd.DataFrame({
            "application_id": [f"A{i}" for i in range(12)],
            "segment": ["Large"] * 8 + ["Small"] * 2 + ["One class"] * 2,
            "default": [0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 0],
            "probability_default": [.1, .8, .2, .7, .3, .6, .4, .5, .1, .9, .2, .3],
        })

    def test_metrics_threshold_errors_and_deterministic_intervals(self):
        first = subgroup_diagnostics(self.frame, "segment", threshold=.5, min_group_size=4, bootstrap_draws=200, seed=9)
        second = subgroup_diagnostics(self.frame, "segment", threshold=.5, min_group_size=4, bootstrap_draws=200, seed=9)
        pd.testing.assert_frame_equal(first, second)
        large = first[first.group == "Large"].iloc[0]
        self.assertEqual(large.status, "Reported")
        self.assertAlmostEqual(large.roc_auc, 1.0)
        self.assertAlmostEqual(large.true_positive_rate, 1.0)
        self.assertAlmostEqual(large.false_positive_rate, 0.0)
        self.assertAlmostEqual(large.mean_predicted_pd, .45)
        self.assertAlmostEqual(large.observed_default_rate, .5)

    def test_small_and_one_class_groups_are_suppressed(self):
        result = subgroup_diagnostics(self.frame, "segment", min_group_size=2, bootstrap_draws=100)
        self.assertIn("one observed outcome", result.set_index("group").loc["One class", "status"])
        result = subgroup_diagnostics(self.frame, "segment", min_group_size=3, bootstrap_draws=100)
        self.assertIn("below minimum", result.set_index("group").loc["Small", "status"])
        self.assertTrue(np.isnan(result.set_index("group").loc["Small", "roc_auc"]))

    def test_age_band_and_group_allowlist(self):
        frame = self.frame.assign(age=[22, 31, 42, 55, 65, 29, 39, 49, 59, 69, 25, 35], employment_status=["A", "B"] * 6)
        enriched = add_audit_groups(frame)
        self.assertIn("age_band", enriched)
        self.assertEqual(available_group_columns(frame), ["employment_status", "age_band"])

    def test_invalid_parameters_and_fields_are_rejected(self):
        for kwargs in ({"threshold": 0}, {"min_group_size": 1}, {"bootstrap_draws": 99}):
            with self.assertRaises(ValueError):
                subgroup_diagnostics(self.frame, "segment", **kwargs)
        with self.assertRaisesRegex(ValueError, "Missing subgroup fields"):
            subgroup_diagnostics(self.frame, "unknown")

    def test_intersection_combines_only_supported_distinct_fields(self):
        frame = self.frame.assign(
            age=[22, 31, 42, 55, 65, 29, 39, 49, 59, 69, 25, 35],
            employment_status=["Employed", "Other"] * 6,
        )
        result = add_intersection_group(frame, "employment_status", "age_band")
        self.assertIn("intersection", result)
        self.assertTrue(result.intersection.str.contains(" × ", regex=False).all())
        with self.assertRaisesRegex(ValueError, "different"):
            add_intersection_group(frame, "age_band", "age_band")
        with self.assertRaisesRegex(ValueError, "supported"):
            add_intersection_group(frame, "employment_status", "application_id")


if __name__ == "__main__":
    unittest.main()

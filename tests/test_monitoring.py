import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import unittest
import numpy as np
import pandas as pd

from monitoring import categorical_psi, feature_drift_table, numeric_psi, score_drift_summary


class MonitoringTests(unittest.TestCase):
    def test_identical_distributions_have_zero_psi(self):
        numeric = pd.Series(np.arange(100, dtype=float))
        category = pd.Series(["A", "B"] * 50)
        self.assertAlmostEqual(numeric_psi(numeric, numeric), 0.0)
        self.assertAlmostEqual(categorical_psi(category, category), 0.0)

    def test_shift_and_unseen_categories_are_detected(self):
        reference = pd.DataFrame({"amount": np.arange(100), "type": ["A", "B"] * 50})
        current = pd.DataFrame({"amount": np.arange(100) + 100, "type": ["C"] * 100})
        result = feature_drift_table(reference, current, ["amount"], ["type"])
        self.assertTrue((result.psi > .25).all())
        self.assertTrue((result.shift_signal == "Higher shift signal").all())

    def test_missingness_change_and_constant_reference(self):
        reference = pd.DataFrame({"value": [1.0] * 10, "kind": ["A"] * 10})
        current = pd.DataFrame({"value": [1.0] * 5 + [np.nan] * 5, "kind": ["A"] * 10})
        result = feature_drift_table(reference, current, ["value"], ["kind"])
        value = result.set_index("feature").loc["value"]
        self.assertEqual(value.current_missing_rate, .5)
        self.assertGreater(value.psi, 0)

    def test_score_summary_and_validation(self):
        result = score_drift_summary([.1, .2, .3, .4], [.2, .3, .4, .5], bins=2)
        self.assertAlmostEqual(result["mean_pd_change"], .1)
        with self.assertRaises(ValueError):
            score_drift_summary([], [.1])
        with self.assertRaises(ValueError):
            numeric_psi(pd.Series([1, 2]), pd.Series([1, 2]), bins=1)


if __name__ == "__main__":
    unittest.main()

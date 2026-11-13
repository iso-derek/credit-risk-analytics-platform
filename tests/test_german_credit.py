"""German Credit (UCI Statlog) parser tests, using rows built from the official codes (no download)."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from data_sources import GERMAN_CATEGORICAL, GERMAN_NUMERIC, german_credit_dataset  # noqa: E402

CODE_CHOICES = [
    ["A11", "A12", "A13", "A14"], None, ["A30", "A32", "A34"], ["A40", "A43", "A49"], None, ["A61", "A65"],
    ["A71", "A73", "A75"], None, ["A91", "A92", "A93", "A95"], ["A101", "A103"], None, ["A121", "A124"], None,
    ["A141", "A143"], ["A151", "A152"], None, ["A172", "A173"], None, ["A191", "A192"], ["A201", "A202"],
]


def sample_rows(count: int = 240) -> str:
    lines = []
    for i in range(count):
        values = []
        for position, choices in enumerate(CODE_CHOICES):
            if choices:
                values.append(choices[i % len(choices)])
            else:
                values.append(str({1: 6 + i % 40, 4: 500 + 37 * i, 7: 1 + i % 4, 10: 1 + i % 4, 12: 20 + i % 50,
                                   15: 1 + i % 3, 17: 1 + i % 2}[position]))
        values.append("2" if i % 3 == 0 else "1")  # class: 1 good, 2 bad
        lines.append(" ".join(values))
    return "\n".join(lines)


class GermanCreditTests(unittest.TestCase):
    def setUp(self):
        self.df, self.spec = german_credit_dataset(sample_rows())

    def test_codes_become_plain_english(self):
        row = self.df.iloc[0]
        self.assertEqual(row.checking_account, "Overdrawn (below 0 DM)")
        self.assertEqual(row.purpose, "New car")
        self.assertEqual(row.sex, "Male")
        self.assertEqual(row.application_id, "DE-0001")
        self.assertEqual(row.default, 1)  # class 2 = bad credit risk

    def test_protected_characteristics_are_never_model_inputs(self):
        inputs = set(GERMAN_NUMERIC + GERMAN_CATEGORICAL)
        for protected in ["sex", "age", "foreign_worker", "personal_status_sex"]:
            self.assertNotIn(protected, inputs)
        self.assertEqual(set(self.spec["protected_fields"]), {"sex", "age", "foreign_worker"})
        self.assertIn("sex", self.df)  # still available for the fairness diagnostics

    def test_unknown_codes_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "Unknown German Credit codes"):
            german_credit_dataset(sample_rows().replace("A11", "A19", 1))


if __name__ == "__main__":
    unittest.main()

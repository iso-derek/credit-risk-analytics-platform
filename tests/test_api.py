"""Contract tests for the JSON API behind the React web app (synthetic data only)."""
import unittest

from fastapi.testclient import TestClient

from api.main import app


class ApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def get(self, url):
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    def test_meta_describes_every_model_input_in_plain_english(self):
        meta = self.get("/api/meta")
        self.assertTrue(meta["synthetic"])
        self.assertEqual(meta["currency"], "USD")
        self.assertEqual([band["letter"] for band in meta["bands"]], list("ABCDE"))
        for field in meta["fields"]:
            self.assertNotIn("_", field["label"], field)

    def test_overview_totals_match_bands(self):
        overview = self.get("/api/overview")
        kpis = overview["kpis"]
        self.assertEqual(sum(band["applicants"] for band in overview["bands"]), kpis["applicants"])
        self.assertAlmostEqual(sum(band["expected_loss"] for band in overview["bands"]), kpis["expected_loss"], places=4)
        histogram_total = sum(row[letter] for row in overview["histogram"] for letter in "ABCDE")
        self.assertEqual(histogram_total, kpis["applicants"])

    def test_segments_reject_unknown_fields(self):
        self.assertEqual(self.client.get("/api/segments?by=application_id").status_code, 400)
        rows = self.get("/api/segments?by=loan_purpose")["rows"]
        self.assertAlmostEqual(sum(row["expected_loss_share"] for row in rows), 1.0, places=9)

    def test_applicant_list_filters_sorts_and_pages(self):
        page = self.get("/api/applicants?band=E&sort=risk&limit=5")
        risks = [row["probability_default"] for row in page["rows"]]
        self.assertEqual(risks, sorted(risks, reverse=True))
        self.assertTrue(all(row["credit_score_band"].startswith("E") for row in page["rows"]))
        self.assertLessEqual(len(page["rows"]), 5)

    def test_applicant_profile_has_readable_drivers(self):
        first = self.get("/api/applicants?limit=1")["rows"][0]["application_id"]
        profile = self.get(f"/api/applicants/{first}")
        self.assertGreater(len(profile["drivers"]), 0)
        for driver in profile["drivers"]:
            self.assertNotIn("_", driver["label"])
        self.assertEqual(self.client.get("/api/applicants/NOT-AN-ID").status_code, 404)

    def test_neutral_scenario_matches_baseline_and_stress_raises_loss(self):
        neutral = self.get("/api/scenario?odds=1&lgd=0.45&exposure=1")
        self.assertAlmostEqual(neutral["change"], 0.0, places=6)
        stressed = self.get("/api/scenario?odds=2&lgd=0.6&exposure=1.1")
        self.assertGreater(stressed["change"], 0)
        self.assertEqual(self.client.get("/api/scenario?odds=0").status_code, 422)

    def test_models_drift_and_fairness_respond(self):
        models = self.get("/api/models")
        self.assertEqual(sum(model["selected"] for model in models["models"]), 1)
        drift = self.get("/api/drift")
        self.assertIn("psi", drift["score"])
        fairness = self.get("/api/fairness?group=employment_status&second=home_ownership")
        self.assertTrue(fairness["rows"])
        self.assertEqual(self.client.get("/api/fairness?group=application_id").status_code, 400)

    def test_downloads(self):
        response = self.client.get("/api/downloads/scenario?odds=1.5")
        self.assertEqual(response.status_code, 200)
        self.assertIn("scenario_expected_loss", response.text.splitlines()[0])


if __name__ == "__main__":
    unittest.main()

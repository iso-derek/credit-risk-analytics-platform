from pathlib import Path
import copy
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from governance import evaluate_release_gate, load_release_gate, require_release_ready


ROOT = Path(__file__).resolve().parents[1]


class GovernanceTests(unittest.TestCase):
    def test_current_gate_verifies_evidence_and_preserves_real_blockers(self):
        report = evaluate_release_gate(load_release_gate(), ROOT)
        self.assertFalse(report["release_ready"])
        self.assertEqual(report["criteria_complete"], 4)
        self.assertEqual(report["criteria_blocked"], 4)
        self.assertIn("external_or_temporal_validation", [item["id"] for item in report["blockers"]])

    def test_missing_declared_evidence_becomes_a_blocker(self):
        gate = copy.deepcopy(load_release_gate())
        gate["criteria"][0]["evidence_path"] = "docs/does-not-exist.md"
        report = evaluate_release_gate(gate, ROOT)
        blocker = next(item for item in report["blockers"] if item["id"] == "research_protocol")
        self.assertIn("missing", blocker["blocker"])

    def test_evidence_cannot_escape_repository(self):
        gate = copy.deepcopy(load_release_gate())
        gate["criteria"][0]["evidence_path"] = "../outside.md"
        with self.assertRaisesRegex(ValueError, "escapes"):
            evaluate_release_gate(gate, ROOT)

    def test_ready_gate_requires_all_evidence(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            evidence = Path(directory) / "accepted.md"
            evidence.write_text("accepted", encoding="utf-8")
            relative = evidence.relative_to(ROOT).as_posix()
            gate = {"schema_version": 1, "release_name": "test", "criteria": [{
                "id": "accepted", "category": "test", "description": "accepted",
                "owner_role": "Test Owner", "state": "complete", "evidence_path": relative,
            }]}
            report = evaluate_release_gate(gate, ROOT)
            self.assertTrue(report["release_ready"])
            require_release_ready(report)

    def test_blocked_gate_cannot_be_asserted_ready(self):
        report = evaluate_release_gate(load_release_gate(), ROOT)
        with self.assertRaisesRegex(RuntimeError, "Stable release is blocked"):
            require_release_ready(report)


if __name__ == "__main__":
    unittest.main()

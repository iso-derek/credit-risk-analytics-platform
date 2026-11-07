"""Launcher checks do not install dependencies or spawn servers."""
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("project_launcher", ROOT / "launch.py")
launcher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(launcher)

class LauncherTests(unittest.TestCase):
    def test_run_identifiers_are_unique(self):
        self.assertNotEqual(launcher.new_run_id(), launcher.new_run_id())

    def test_project_entry_points_exist(self):
        self.assertTrue((ROOT / launcher.CONFIG["app"]).is_file())
        self.assertTrue((ROOT / "scripts/run_research.py").is_file())
        self.assertGreaterEqual(launcher.CONFIG["port"], 1024)

    def test_hash_is_stable(self):
        path = ROOT / "project.json"
        self.assertEqual(launcher.digest(path), launcher.digest(path))
        self.assertEqual(len(launcher.digest(path)), 64)

    def test_failed_research_is_recorded_with_artifact_hash(self):
        import json
        import sys
        import tempfile
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "scripts").mkdir()
            (root / "scripts/run_research.py").write_text(
                "from pathlib import Path\n"
                "Path('outputs').mkdir()\n"
                "Path('outputs/sample.csv').write_text('value\\n1\\n')\n"
                "print('Deliberate fixture failure')\n"
                "raise SystemExit(7)\n"
            )
            with patch.object(launcher, "ROOT", root):
                code = launcher.record_research(sys.executable, [])
            self.assertEqual(code, 7)
            folders = list((root / "runs").iterdir())
            self.assertEqual(len(folders), 1)
            manifest = json.loads((folders[0] / "manifest.json").read_text())
            self.assertEqual(manifest["exit_code"], 7)
            self.assertEqual(manifest["artifacts_changed_by_run"][0]["sha256"],
                             launcher.digest(folders[0] / "outputs/sample.csv"))
            self.assertIn("Deliberate fixture failure", (folders[0] / "execution.log").read_text())


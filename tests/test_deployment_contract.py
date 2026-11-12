from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class DeploymentContractTests(unittest.TestCase):
    def test_container_uses_tested_python_and_non_root_runtime(self):
        dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
        self.assertIn("FROM python:3.13-slim", dockerfile)
        self.assertIn("requirements-tested.txt", dockerfile)
        self.assertIn("USER app", dockerfile)
        self.assertNotIn("USER root", dockerfile)

    def test_container_has_loopback_health_contract(self):
        dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
        self.assertIn("HEALTHCHECK", dockerfile)
        self.assertIn("127.0.0.1:8502/_stcore/health", dockerfile)
        self.assertIn('"--server.address=0.0.0.0"', dockerfile)

    def test_build_context_excludes_local_and_evidence_data(self):
        ignored = set((ROOT / ".dockerignore").read_text(encoding="utf-8").splitlines())
        self.assertTrue({".git", ".env", ".venv", "data", "outputs", "runs"} <= ignored)

    def test_ci_builds_smokes_and_cleans_up_container(self):
        workflow = (ROOT / ".github" / "workflows" / "container.yml").read_text(encoding="utf-8")
        self.assertIn("docker build", workflow)
        self.assertIn("docker exec credit-risk-app id -u", workflow)
        self.assertIn("/_stcore/health", workflow)
        self.assertIn("docker rm --force", workflow)


if __name__ == "__main__":
    unittest.main()

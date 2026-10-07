"""Portable setup, dashboard launch, tests and recorded research runs.

Run python launch.py; no environment activation or administrator access required.
"""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import hashlib
import importlib.metadata
import json
import shutil
import subprocess
import sys
import uuid

ROOT = Path(__file__).resolve().parent
CONFIG = json.loads((ROOT / "project.json").read_text())
PACKAGES = ["numpy", "pandas", "scipy", "scikit-learn", "streamlit", "plotly"]

def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def artifacts():
    folder = ROOT / "outputs"
    return {str(p.relative_to(ROOT)): digest(p) for p in folder.rglob("*")
            if p.is_file() and p.suffix in {".csv", ".json", ".zip", ".txt"}} if folder.exists() else {}

def new_run_id():
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:8]

def python_environment():
    if sys.version_info[:2] not in {(3, 12), (3, 13)}:
        raise SystemExit("Use Python 3.12 or 3.13; these are the compatibility-test targets.")
    environment = ROOT / ".venv"
    interpreter = environment / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
    if not interpreter.exists():
        subprocess.run([sys.executable, "-m", "venv", str(environment)], check=True)
    fingerprint = digest(ROOT / "requirements.txt") + digest(ROOT / "requirements-tested.txt")
    marker = environment / ".project-requirements"
    if not marker.exists() or marker.read_text() != fingerprint:
        subprocess.run([str(interpreter), "-m", "pip", "install", "-r",
                        str(ROOT / "requirements-tested.txt")], check=True, cwd=ROOT)
        marker.write_text(fingerprint)
    return str(interpreter)

def record_research(interpreter, extra):
    folder = ROOT / "runs" / new_run_id()
    folder.mkdir(parents=True, exist_ok=False)
    before = artifacts()
    command = [interpreter, "scripts/run_research.py", *extra]
    git = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True)
    dirty = subprocess.run(["git", "status", "--porcelain"], cwd=ROOT, capture_output=True, text=True)
    versions = subprocess.run([interpreter, "-c", "import importlib.metadata as m; print('\\n'.join(sorted(d.metadata['Name']+'=='+d.version for d in m.distributions())))"], capture_output=True, text=True, check=True)
    started = datetime.now(timezone.utc).isoformat()
    with (folder / "execution.log").open("w", encoding="utf-8") as log:
        process = subprocess.Popen(command, cwd=ROOT, stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace")
        for line in process.stdout:
            print(line, end="", flush=True)
            log.write(line)
        code = process.wait()
        process.stdout.close()
    snapshots = []
    for relative, checksum in artifacts().items():
        if before.get(relative) == checksum:
            continue
        source = ROOT / relative
        destination = folder / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        snapshots.append({"path": relative, "sha256": checksum})
    manifest = {"schema_version": 1, "project": CONFIG["name"], "command": command[1:],
                "started_at": started, "finished_at": datetime.now(timezone.utc).isoformat(),
                "exit_code": code, "git_commit": git.stdout.strip() if git.returncode == 0 else None,
                "worktree_dirty": bool(dirty.stdout.strip()) if dirty.returncode == 0 else None,
                "artifacts_changed_by_run": snapshots,
                "limitations": "Only changed outputs are snapshotted. Inspect logs for data provenance; success is not evidence of research validity."}
    (folder / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    (folder / "dependencies.txt").write_text(versions.stdout, encoding="utf-8")
    print("Recorded research run:", folder)
    return code

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=["dashboard", "tests", "research", "setup"], nargs="?", default="dashboard")
    parser.add_argument("--port", type=int, default=CONFIG["port"])
    parser.add_argument("--research-ui", action="store_true")
    args, extra = parser.parse_known_args()
    if extra and args.mode != "research":
        parser.error("Additional arguments are only forwarded in research mode.")
    if not 1024 <= args.port <= 65535:
        parser.error("Port must be between 1024 and 65535.")
    interpreter = python_environment()
    if args.mode == "setup":
        return 0
    if args.mode == "tests":
        return subprocess.run([interpreter, "-m", "unittest", "discover", "-s", "tests", "-v"], cwd=ROOT).returncode
    if args.mode == "research":
        return record_research(interpreter, extra)
    app = CONFIG.get("research_app") if args.research_ui else CONFIG["app"]
    if not app:
        parser.error("This project does not have a separate research dashboard.")
    return subprocess.run([interpreter, "-m", "streamlit", "run", app,
                           "--server.address", "127.0.0.1", "--server.port", str(args.port)], cwd=ROOT).returncode

if __name__ == "__main__":
    raise SystemExit(main())

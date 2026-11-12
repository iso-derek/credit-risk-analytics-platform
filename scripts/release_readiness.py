"""Print the current stable-release gate report; exits 2 while blockers remain."""
from pathlib import Path
import argparse
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from governance import evaluate_release_gate, load_release_gate


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--gate", type=Path, default=ROOT / "config" / "release_gate.json")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = evaluate_release_gate(load_release_gate(args.gate), ROOT)
    payload = json.dumps(report, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload + "\n", encoding="utf-8")
    print(payload)
    raise SystemExit(0 if report["release_ready"] else 2)

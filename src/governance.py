"""Machine-checkable release evidence and unresolved approval gates."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import json


DEFAULT_GATE = Path(__file__).resolve().parents[1] / "config" / "release_gate.json"


def load_release_gate(path: Path | str = DEFAULT_GATE) -> dict:
    gate = json.loads(Path(path).read_text(encoding="utf-8"))
    if gate.get("schema_version") != 1 or not gate.get("release_name"):
        raise ValueError("Release gate requires schema version 1 and a release name.")
    criteria = gate.get("criteria")
    if not isinstance(criteria, list) or not criteria:
        raise ValueError("Release gate requires at least one criterion.")
    ids = [item.get("id") for item in criteria]
    if any(not value for value in ids) or len(ids) != len(set(ids)):
        raise ValueError("Release criterion IDs must be unique and non-empty.")
    for item in criteria:
        missing = {"category", "description", "owner_role", "state"} - set(item)
        if missing:
            raise ValueError(f"Criterion {item['id']} is missing: {sorted(missing)}")
        if item["state"] not in {"complete", "blocked"}:
            raise ValueError(f"Criterion {item['id']} has an invalid state.")
        if item["state"] == "complete" and not item.get("evidence_path"):
            raise ValueError(f"Complete criterion {item['id']} requires evidence.")
        if item["state"] == "blocked" and not item.get("blocker"):
            raise ValueError(f"Blocked criterion {item['id']} requires a blocker.")
    return gate


def evaluate_release_gate(gate: dict, repository_root: Path | str) -> dict:
    root = Path(repository_root).resolve()
    results = []
    for item in gate["criteria"]:
        result = dict(item)
        if item["state"] == "complete":
            evidence = (root / item["evidence_path"]).resolve()
            try:
                evidence.relative_to(root)
            except ValueError as exc:
                raise ValueError(f"Evidence for {item['id']} escapes the repository.") from exc
            if not evidence.is_file():
                result["state"] = "blocked"
                result["blocker"] = f"Declared evidence file is missing: {item['evidence_path']}"
            else:
                result["evidence_verified"] = True
        results.append(result)
    blockers = [
        {"id": item["id"], "category": item["category"], "owner_role": item["owner_role"],
         "blocker": item["blocker"]}
        for item in results if item["state"] == "blocked"
    ]
    return {
        "schema_version": gate["schema_version"],
        "release_name": gate["release_name"],
        "evaluated_at_utc": datetime.now(timezone.utc).isoformat(),
        "release_ready": not blockers,
        "criteria_total": len(results),
        "criteria_complete": len(results) - len(blockers),
        "criteria_blocked": len(blockers),
        "blockers": blockers,
        "criteria": results,
        "decision_note": "Technical evidence does not override required human approvals or validation evidence.",
    }


def require_release_ready(report: dict) -> None:
    if not report.get("release_ready"):
        ids = ", ".join(item["id"] for item in report.get("blockers", []))
        raise RuntimeError(f"Stable release is blocked by: {ids}")

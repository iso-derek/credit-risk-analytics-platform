"""Validate a timestamped CSV cohort without fitting or changing a model."""
from pathlib import Path
import argparse
import json
import sys

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from monitoring_ops import load_monitoring_policy, outcome_maturity_summary, validate_timestamped_cohort


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("cohort", type=Path)
    parser.add_argument("--features", nargs="+", required=True)
    parser.add_argument("--as-of", required=True, help="ISO-8601 monitoring cutoff")
    parser.add_argument("--policy", type=Path, default=Path("config/monitoring_policy.json"))
    parser.add_argument("--timestamp-column", default="observed_at")
    parser.add_argument("--outcome-column", default="default")
    args = parser.parse_args()
    policy = load_monitoring_policy(args.policy)
    cohort = pd.read_csv(args.cohort)
    report = {
        "cohort": validate_timestamped_cohort(
            cohort, args.features, as_of=args.as_of, timestamp_column=args.timestamp_column,
            minimum_rows=policy["minimum_cohort_rows"],
        )
    }
    if args.outcome_column in cohort:
        report["outcomes"] = outcome_maturity_summary(
            cohort, as_of=args.as_of, outcome_lag_days=policy["outcome_lag_days"],
            timestamp_column=args.timestamp_column, outcome_column=args.outcome_column,
        )
    print(json.dumps(report, indent=2))

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from family_doctor.report_pipeline import run_report_pipeline


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the family doctor report pipeline.")
    parser.add_argument("--event", required=True, type=Path)
    parser.add_argument("--target", required=True, type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    try:
        result = run_report_pipeline(args.event, args.target)
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1

    json.dump(result, sys.stdout, ensure_ascii=False)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

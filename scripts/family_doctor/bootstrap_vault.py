from __future__ import annotations

import argparse
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CANONICAL_ROOT = ROOT / "family-health"


class BootstrapError(ValueError):
    """Raised when bootstrap preconditions are not satisfied."""


def validate_bootstrap_paths(target: Path) -> tuple[Path, Path]:
    canonical_root = CANONICAL_ROOT.resolve()
    resolved_target = target.resolve()

    if not CANONICAL_ROOT.exists():
        raise BootstrapError(f"Canonical root does not exist: {CANONICAL_ROOT}")

    if not CANONICAL_ROOT.is_dir():
        raise BootstrapError(f"Canonical root is not a directory: {CANONICAL_ROOT}")

    if resolved_target == canonical_root or canonical_root in resolved_target.parents:
        raise BootstrapError(
            f"Target must not be the canonical root or inside it: {resolved_target}"
        )

    return canonical_root, resolved_target


def copy_missing(src: Path, dst: Path, logs: list[str]) -> None:
    for path in sorted(src.rglob("*")):
        relative_path = path.relative_to(src)
        target_path = dst / relative_path

        if path.is_dir():
            target_path.mkdir(parents=True, exist_ok=True)
            continue

        target_path.parent.mkdir(parents=True, exist_ok=True)
        if target_path.exists():
            logs.append(f"skipped {target_path}")
            continue

        target_path.write_bytes(path.read_bytes())
        logs.append(f"copied {target_path}")


def bootstrap(target: Path) -> list[str]:
    canonical_root, resolved_target = validate_bootstrap_paths(target)
    logs: list[str] = []
    resolved_target.mkdir(parents=True, exist_ok=True)
    copy_missing(canonical_root, resolved_target, logs)
    return logs


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Copy the canonical family-health scaffold into a target directory."
    )
    parser.add_argument("--target", required=True, type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    try:
        for line in bootstrap(args.target):
            print(line)
    except BootstrapError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

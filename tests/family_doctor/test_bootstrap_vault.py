import argparse
import importlib.util
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
BOOTSTRAP = ROOT / "scripts" / "family_doctor" / "bootstrap_vault.py"

EXPECTED_TRACKING_FILES = [
    "体检指标.csv",
    "用药打卡.csv",
    "饮食记录.csv",
    "运动记录.csv",
    "睡眠记录.csv",
]

EXPECTED_OUTPUT_DIRECTORIES = [
    "checkup-updates",
    "lab-updates",
    "visit-briefs",
    "family-messages",
    "weekly-reports",
    "monthly-reports",
    "reminder-messages",
    "qa-summaries",
]

EXPECTED_PAGE_TEMPLATES = [
    "family-message-template.md",
    "visit-brief-template.md",
]


def load_bootstrap_module():
    spec = importlib.util.spec_from_file_location("bootstrap_vault_test_module", BOOTSTRAP)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_bootstrap_copies_full_phase0_topology(run_bootstrap, tmp_path):
    target = tmp_path / "family-health"
    result = run_bootstrap(target)

    assert result.returncode == 0
    assert (target / "00_schema" / "event-schema.json").exists()
    assert (target / "家庭健康管理中心.md").exists()
    assert (target / "02_wiki" / "members").exists()
    assert (target / "99_runtime" / "jobs").exists()
    assert not (target / "family-health").exists()

    for filename in EXPECTED_TRACKING_FILES:
        assert (target / "04_tracking" / filename).exists(), filename

    for directory in EXPECTED_OUTPUT_DIRECTORIES:
        assert (target / "03_outputs" / directory).is_dir(), directory

    for filename in EXPECTED_PAGE_TEMPLATES:
        assert (target / "00_schema" / "page-templates" / filename).exists(), filename


def test_bootstrap_is_idempotent(run_bootstrap, tmp_path):
    target = tmp_path / "family-health"
    first = run_bootstrap(target)
    second = run_bootstrap(target)

    assert first.returncode == 0
    assert second.returncode == 0
    assert "copied" in first.stdout.lower()
    assert "skipped" in second.stdout.lower() or "already exists" in second.stdout.lower()


@pytest.mark.parametrize("canonical_root_kind", ["missing", "file"])
def test_bootstrap_fails_when_canonical_root_is_invalid(
    tmp_path, monkeypatch, capsys, canonical_root_kind
):
    module = load_bootstrap_module()
    canonical_root = tmp_path / "canonical-root"
    target = tmp_path / "bootstrapped-copy"

    if canonical_root_kind == "file":
        canonical_root.write_text("not a directory", encoding="utf-8")

    monkeypatch.setattr(module, "CANONICAL_ROOT", canonical_root)
    monkeypatch.setattr(module, "parse_args", lambda: argparse.Namespace(target=target))

    exit_code = module.main()
    captured = capsys.readouterr()

    assert exit_code != 0
    assert captured.out == ""
    assert "canonical root" in captured.err.lower()
    assert not target.exists()


def test_bootstrap_rejects_target_inside_canonical_root(tmp_path, monkeypatch, capsys):
    module = load_bootstrap_module()
    canonical_root = tmp_path / "canonical-root"
    source_file = canonical_root / "00_schema" / "event-schema.json"
    source_file.parent.mkdir(parents=True)
    source_file.write_text("{}", encoding="utf-8")
    target = canonical_root / "nested-copy"

    monkeypatch.setattr(module, "CANONICAL_ROOT", canonical_root)
    monkeypatch.setattr(module, "parse_args", lambda: argparse.Namespace(target=target))

    exit_code = module.main()
    captured = capsys.readouterr()

    assert exit_code != 0
    assert captured.out == ""
    assert "inside" in captured.err.lower() or "within" in captured.err.lower()
    assert not target.exists()

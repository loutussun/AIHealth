from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_run_ingest_archives_report_and_writes_source_page(
    run_bootstrap, run_ingest, tmp_path
):
    target = tmp_path / "family-health"
    event = ROOT / "tests" / "family_doctor" / "fixtures" / "events" / "checkup-report.json"
    assert run_bootstrap(target).returncode == 0

    result = run_ingest(event, target)

    assert result.returncode == 0
    assert list((target / "02_wiki" / "sources").glob("*.md"))
    assert "ingest completed" in result.stdout.lower()

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_same_day_distinct_reports_generate_distinct_source_ids(
    run_bootstrap, run_ingest, tmp_path
):
    target = tmp_path / "family-health"
    first_event = ROOT / "tests" / "family_doctor" / "fixtures" / "events" / "lab-report.json"
    second_event = (
        ROOT
        / "tests"
        / "family_doctor"
        / "fixtures"
        / "events"
        / "lab-report-second.json"
    )
    assert run_bootstrap(target).returncode == 0

    assert run_ingest(first_event, target).returncode == 0
    assert run_ingest(second_event, target).returncode == 0

    source_pages = sorted((target / "02_wiki" / "sources").glob("*.md"))
    assert len(source_pages) == 2
    assert source_pages[0].name != source_pages[1].name

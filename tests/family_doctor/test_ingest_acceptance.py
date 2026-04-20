from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def read_source_id(source_page: Path) -> str:
    content = source_page.read_text(encoding="utf-8")
    lines = content.splitlines()
    if lines[0] != "---":
        raise AssertionError("source page missing frontmatter")

    for line in lines[1:]:
        if line == "---":
            break
        if line.startswith("source_id:"):
            return line.split(":", 1)[1].strip()

    raise AssertionError("source page missing source_id")


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
    assert read_source_id(source_pages[0]) != read_source_id(source_pages[1])

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

EXPECTED_TRACKING_FILES = {
    "体检指标.csv": "member_id,date,item,result,unit,reference_range,status,source_ref,notes",
    "用药打卡.csv": "member_id,date,time,medication_id,dose,status,source_ref,notes",
    "饮食记录.csv": "member_id,date,meal,summary,tags,source_ref,notes",
    "运动记录.csv": "member_id,date,activity,duration_minutes,intensity,source_ref,notes",
    "睡眠记录.csv": "member_id,date,sleep_start,sleep_end,duration_hours,quality,source_ref,notes",
}

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


def test_family_health_home_page_exists_and_links_core_pages():
    home = ROOT / "family-health" / "家庭健康管理中心.md"
    assert home.exists()

    content = home.read_text(encoding="utf-8")
    assert "[[index]]" in content
    assert "[[log]]" in content
    assert "02_wiki/members" in content
    assert "04_tracking/体检指标.csv" in content


def test_tracking_csv_assets_exist_with_expected_headers():
    tracking_dir = ROOT / "family-health" / "04_tracking"

    for filename, expected_header in EXPECTED_TRACKING_FILES.items():
        csv_path = tracking_dir / filename
        assert csv_path.exists(), filename
        first_line = csv_path.read_text(encoding="utf-8").splitlines()[0]
        assert first_line == expected_header


def test_outputs_include_obsidian_first_directories():
    outputs_dir = ROOT / "family-health" / "03_outputs"

    for directory in EXPECTED_OUTPUT_DIRECTORIES:
        assert (outputs_dir / directory).is_dir(), directory


def test_page_templates_include_obsidian_first_outputs():
    template_dir = ROOT / "family-health" / "00_schema" / "page-templates"

    for filename in EXPECTED_PAGE_TEMPLATES:
        template_path = template_dir / filename
        assert template_path.exists(), filename

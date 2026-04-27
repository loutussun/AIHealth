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

EXPECTED_HOME_SECTIONS = [
    "## 家庭成员",
    "## 最近资料",
    "## 待复查与计划",
    "## 给家人的摘要",
    "## 追踪表格",
    "## 维护日志",
]

EXPECTED_INDEX_SECTIONS = [
    "## 人类入口",
    "## 成员",
    "## 原始资料",
    "## Wiki 页面",
    "## 输出",
    "## Tracking CSV",
    "## Runtime",
]

EXPECTED_LOG_PREFIXES = [
    "[ingest]",
    "[query]",
    "[report]",
    "[reminder]",
    "[lint]",
    "[manual-review]",
]

EXPECTED_MEMBER_TEMPLATE_HEADINGS = [
    "## 基本信息",
    "## 成员识别与代理关系",
    "## 重要病史",
    "## 过敏史与禁忌",
    "## 当前用药",
    "## 最近关键指标",
    "## 近期就医/检查",
    "## 当前计划",
    "## 待核实项",
    "## 来源索引",
]

EXPECTED_SOURCE_TEMPLATE_HEADINGS = [
    "## 来源信息",
    "## 提取事实",
    "## 异常项",
    "## 影响到的 Wiki 页面",
    "## 待核实项",
]

EXPECTED_FAMILY_MESSAGE_TEMPLATE_HEADINGS = [
    "## 面向对象",
    "## 可发送消息",
    "## 依据来源",
    "## 不确定项",
]

EXPECTED_VISIT_BRIEF_TEMPLATE_HEADINGS = [
    "## 就医目标",
    "## 一页纸摘要",
    "## 当前用药",
    "## 近期关键检查",
    "## 建议追问医生的问题",
    "## 就医后记录模板",
    "## 依据来源",
]


def test_family_health_home_page_exists_and_links_core_pages():
    home = ROOT / "family-health" / "家庭健康管理中心.md"
    assert home.exists()

    content = home.read_text(encoding="utf-8")
    assert "type: health-hub" in content
    assert "purpose: 家庭健康管理入口" in content
    assert "[[index" in content
    assert "[[log]]" in content
    assert "02_wiki/members" in content
    assert "04_tracking/体检指标.csv" in content
    for section in EXPECTED_HOME_SECTIONS:
        assert section in content


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


def test_index_is_structured_as_llm_navigation_surface():
    index = ROOT / "family-health" / "index.md"
    content = index.read_text(encoding="utf-8")

    assert "[[家庭健康管理中心]]" in content
    for section in EXPECTED_INDEX_SECTIONS:
        assert section in content


def test_log_documents_stable_operation_prefixes():
    log = ROOT / "family-health" / "log.md"
    content = log.read_text(encoding="utf-8")

    for prefix in EXPECTED_LOG_PREFIXES:
        assert prefix in content


def test_agents_rules_preserve_obsidian_first_boundaries():
    agents = ROOT / "family-health" / "AGENTS.md"
    content = agents.read_text(encoding="utf-8")

    for policy_id in [
        "policy: vault-product-surface",
        "policy: source-grounded-medical-assertions",
        "policy: raw-append-only",
        "policy: runtime-process-state",
        "policy: tracking-preserve-headers",
    ]:
        assert policy_id in content


def test_core_page_templates_match_obsidian_first_headings():
    template_dir = ROOT / "family-health" / "00_schema" / "page-templates"
    expected_headings = {
        "member-template.md": EXPECTED_MEMBER_TEMPLATE_HEADINGS,
        "source-template.md": EXPECTED_SOURCE_TEMPLATE_HEADINGS,
        "family-message-template.md": EXPECTED_FAMILY_MESSAGE_TEMPLATE_HEADINGS,
        "visit-brief-template.md": EXPECTED_VISIT_BRIEF_TEMPLATE_HEADINGS,
    }

    for filename, headings in expected_headings.items():
        content = (template_dir / filename).read_text(encoding="utf-8")
        for heading in headings:
            assert heading in content, f"{filename}: {heading}"

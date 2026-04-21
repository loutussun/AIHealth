from family_doctor.markdown_utils import safe_slug


def test_safe_slug_rewrites_dot_only_values_to_non_traversal_slug():
    assert safe_slug(".") == "item"
    assert safe_slug("..") == "item"
    assert safe_slug("...") == "item"


def test_safe_slug_preserves_safe_identifiers():
    assert safe_slug("dad-plan_2026") == "dad-plan_2026"

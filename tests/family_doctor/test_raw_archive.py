from family_doctor.raw_archive import archive_subdir_for_kind, should_archive_raw


def test_archive_subdir_for_kind_returns_none_for_unknown_kind():
    assert archive_subdir_for_kind("unknown_kind") is None
    assert should_archive_raw("unknown_kind") is False

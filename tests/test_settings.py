from __future__ import annotations

import dataclasses
import json

from streamline import paths, settings


def test_load_returns_defaults_when_no_file_exists():
    result = settings.load()
    assert result == settings.Settings()
    assert result.nickname == "guest"
    assert result.first_run_complete is False


def test_save_then_load_round_trips():
    original = settings.Settings(nickname="alice", web_port=9000, default_interface="web")
    settings.save(original)

    loaded = settings.load()

    assert loaded == original
    assert paths.settings_path().exists()


def test_save_is_atomic_and_leaves_no_tmp_file():
    settings.save(settings.Settings(nickname="bob"))
    assert not paths.settings_path().with_suffix(".tmp").exists()


def test_corrupted_json_falls_back_to_defaults_and_is_quarantined():
    path = paths.settings_path()
    path.write_text("{not valid json", encoding="utf-8")

    result = settings.load()

    assert result == settings.Settings()
    assert not path.exists()
    quarantined = list(path.parent.glob("settings.corrupted-*.json"))
    assert len(quarantined) == 1


def test_non_object_json_falls_back_to_defaults():
    path = paths.settings_path()
    path.write_text(json.dumps([1, 2, 3]), encoding="utf-8")

    result = settings.load()

    assert result == settings.Settings()


def test_unknown_fields_are_ignored_not_fatal():
    path = paths.settings_path()
    path.write_text(json.dumps({"nickname": "carol", "made_up_field": 123}), encoding="utf-8")

    result = settings.load()

    assert result.nickname == "carol"


def test_out_of_range_values_are_reset_to_defaults():
    bad = settings.Settings(
        nickname="x" * 100,
        default_interface="ask",  # type: ignore[arg-type]
        web_port=99999,
        connection_timeout=-5,
    )
    fixed = bad.validated()

    assert fixed.nickname == settings.Settings().nickname
    assert fixed.web_port is None
    assert fixed.connection_timeout == settings.Settings().connection_timeout


def test_invalid_literal_values_reset_to_default():
    path = paths.settings_path()
    path.write_text(
        json.dumps({"default_interface": "not-a-real-choice", "log_level": "verbose"}),
        encoding="utf-8",
    )

    result = settings.load()

    assert result.default_interface == "ask"
    assert result.log_level == "normal"


def test_missing_schema_version_is_migrated():
    path = paths.settings_path()
    path.write_text(json.dumps({"nickname": "dave"}), encoding="utf-8")

    result = settings.load()

    assert result.schema_version == settings.SCHEMA_VERSION
    assert result.nickname == "dave"


def test_passwords_are_never_part_of_the_settings_schema():
    field_names = {f.name for f in dataclasses.fields(settings.Settings)}
    assert not any("password" in name for name in field_names)

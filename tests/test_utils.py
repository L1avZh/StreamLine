from __future__ import annotations

import json

from streamline.utils import (
    constant_time_equals,
    find_free_port,
    get_config_value,
    load_config,
    sanitize_text,
    validate_nickname,
)


def test_get_config_value_returns_default_when_key_missing():
    config = {"existing_key": "value"}
    assert get_config_value(config, "missing_key", "default") == "default"


def test_get_config_value_returns_existing_value_when_key_present():
    config = {"existing_key": "value"}
    assert get_config_value(config, "existing_key", "default") == "value"


def test_get_config_value_falls_back_when_value_is_none():
    config = {"key": None}
    assert get_config_value(config, "key", "default") == "default"


def test_find_free_port_returns_int():
    port = find_free_port()
    assert isinstance(port, int) and 0 < port < 65536


def test_load_config_missing_file_returns_empty_dict(tmp_path):
    assert load_config(tmp_path / "does-not-exist.json") == {}


def test_load_config_invalid_json_returns_empty_dict(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text("{not valid json")
    assert load_config(path) == {}


def test_load_config_non_object_json_returns_empty_dict(tmp_path):
    path = tmp_path / "list.json"
    path.write_text(json.dumps([1, 2, 3]))
    assert load_config(path) == {}


def test_load_config_valid_file(tmp_path):
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"host": "0.0.0.0"}))
    assert load_config(path) == {"host": "0.0.0.0"}


def test_sanitize_text_strips_ansi_escape_sequences():
    malicious = "\x1b[31mred text\x1b[0m"
    assert sanitize_text(malicious) == "red text"


def test_sanitize_text_strips_control_characters():
    assert sanitize_text("hello\x07world") == "helloworld"


def test_sanitize_text_preserves_plain_text():
    assert sanitize_text("hello world") == "hello world"


def test_validate_nickname_accepts_normal_names():
    assert validate_nickname("alice") == "alice"
    assert validate_nickname("alice_02.b-c") == "alice_02.b-c"


def test_validate_nickname_rejects_empty():
    assert validate_nickname("") is None
    assert validate_nickname("   ") is None


def test_validate_nickname_rejects_too_long():
    assert validate_nickname("a" * 33) is None


def test_validate_nickname_rejects_special_characters():
    assert validate_nickname("alice bob") is None
    assert validate_nickname("<script>") is None


def test_constant_time_equals():
    assert constant_time_equals("secret", "secret") is True
    assert constant_time_equals("secret", "wrong") is False

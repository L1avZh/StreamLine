"""Regression tests: StreamLine must degrade gracefully, not crash with a raw
traceback, when its config/log directory isn't writable (locked-down
permissions, a read-only filesystem, a managed environment, ...).

Skipped on Windows: chmod-based read-only directories don't work the same
way there (ACLs, not POSIX mode bits) — this needs a separate Windows-native
reproduction, tracked as an untested platform-specific area rather than
faked here.
"""

from __future__ import annotations

import os
import stat
import sys

import pytest
from click.testing import CliRunner
from fastapi.testclient import TestClient

from streamline import settings as settings_store
from streamline.cli import cli
from streamline.utils import setup_logging
from streamline.web.app import create_app


def _running_as_root() -> bool:
    return hasattr(os, "geteuid") and os.geteuid() == 0


pytestmark = [
    pytest.mark.skipif(
        sys.platform == "win32", reason="POSIX chmod semantics don't apply on Windows"
    ),
    pytest.mark.skipif(_running_as_root(), reason="root ignores POSIX write permission bits"),
]


@pytest.fixture
def readonly_config_dir(tmp_path, monkeypatch):
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    monkeypatch.setenv("STREAMLINE_CONFIG_DIR", str(config_dir))
    settings_store.save(settings_store.Settings())  # create settings.json while writable
    config_dir.chmod(stat.S_IREAD | stat.S_IEXEC)  # read + traverse, no write
    try:
        yield config_dir
    finally:
        config_dir.chmod(stat.S_IRWXU)  # restore so pytest can clean up tmp_path


def test_setup_logging_does_not_crash_when_log_dir_unwritable(readonly_config_dir):
    setup_logging()  # must not raise


def test_cli_version_works_even_with_unwritable_config_dir(readonly_config_dir):
    result = CliRunner().invoke(cli, ["--version"])
    assert result.exit_code == 0
    assert "Traceback" not in result.output


def test_settings_set_fails_cleanly_not_with_a_traceback(readonly_config_dir):
    result = CliRunner().invoke(cli, ["settings", "set", "nickname", "alice"])
    assert result.exit_code != 0
    assert "Traceback" not in result.output
    assert "Could not save settings" in result.output


def test_settings_reset_fails_cleanly_not_with_a_traceback(readonly_config_dir):
    result = CliRunner().invoke(cli, ["settings", "reset"])
    assert result.exit_code != 0
    assert "Traceback" not in result.output
    assert "Could not save settings" in result.output


def test_web_settings_endpoint_returns_clean_error_not_a_crash(readonly_config_dir):
    with TestClient(create_app()) as client:
        response = client.post("/api/settings", json={"nickname": "alice"})
        assert response.status_code == 500
        assert "Could not save settings" in response.json()["detail"]

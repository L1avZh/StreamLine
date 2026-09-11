"""Platform-appropriate storage locations for StreamLine's own data.

User configuration and logs never live inside the installation directory
(the wheel/executable may be read-only, owned by root, or reinstalled at
any time) — they go in the OS-standard per-user locations, resolved by
``platformdirs``: e.g. ``~/Library/Application Support/StreamLine`` on
macOS, ``%APPDATA%\\StreamLine`` on Windows, and XDG paths on Linux.

Set ``STREAMLINE_CONFIG_DIR`` to override this (useful for tests, containers,
or running multiple isolated instances).
"""

from __future__ import annotations

import os
from pathlib import Path

from platformdirs import PlatformDirs

_dirs = PlatformDirs(appname="StreamLine", appauthor=False)


def _override() -> Path | None:
    value = os.environ.get("STREAMLINE_CONFIG_DIR")
    return Path(value).expanduser() if value else None


def config_dir() -> Path:
    """Directory holding ``settings.json``. Created on first use."""
    path = _override() or Path(_dirs.user_config_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path


def settings_path() -> Path:
    return config_dir() / "settings.json"


def log_dir() -> Path:
    """Directory holding StreamLine's own log file. Created on first use."""
    path = _override() or Path(_dirs.user_log_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path


def log_file_path() -> Path:
    return log_dir() / "streamline.log"

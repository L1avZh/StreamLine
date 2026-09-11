"""Persistent user settings — the single source of truth for defaults.

Settings live in the OS-appropriate user config directory (see
:mod:`streamline.paths`), never inside the installation directory, and
never need to be hand-edited: `streamline settings` (CLI) and the web
interface's Settings page both read and write them through this module.

Precedence used throughout the app: explicit CLI flag > environment
variable > saved setting > built-in default.
"""

from __future__ import annotations

import contextlib
import json
import logging
import time
from dataclasses import asdict, dataclass, fields
from pathlib import Path
from typing import Any, Literal, get_args

from .paths import settings_path

logger = logging.getLogger(__name__)

#: Bumped whenever a field is added, removed, or reinterpreted in a way
#: that needs `_migrate` to handle old files.
SCHEMA_VERSION = 1

Interface = Literal["ask", "cli", "web"]
LogLevel = Literal["normal", "debug"]

_ALLOWED_INTERFACE = set(get_args(Interface))
_ALLOWED_LOG_LEVEL = set(get_args(LogLevel))


@dataclass
class Settings:
    schema_version: int = SCHEMA_VERSION
    first_run_complete: bool = False

    # General
    nickname: str = "guest"
    default_interface: Interface = "ask"

    # Connection defaults, used to pre-fill the guided CLI / web "Join" form
    default_host: str = "127.0.0.1"
    default_port: int | None = None
    connection_timeout: float = 10.0

    # Web interface
    web_bind_host: str = "127.0.0.1"
    web_port: int | None = None
    web_open_browser: bool = True

    # Security — deliberately excludes passwords; those are never persisted.
    tls_cafile: str | None = None

    # Advanced
    log_level: LogLevel = "normal"

    def validated(self) -> Settings:
        """Return a copy with any out-of-range values reset to defaults."""
        data = asdict(self)
        defaults = {f.name: f.default for f in fields(Settings)}

        if data["default_interface"] not in _ALLOWED_INTERFACE:
            data["default_interface"] = defaults["default_interface"]
        if data["log_level"] not in _ALLOWED_LOG_LEVEL:
            data["log_level"] = defaults["log_level"]
        nickname = data["nickname"]
        if not isinstance(nickname, str) or not (1 <= len(nickname.strip()) <= 32):
            data["nickname"] = defaults["nickname"]
        for key in ("default_port", "web_port"):
            value = data[key]
            if value is not None and not (isinstance(value, int) and 1 <= value <= 65535):
                data[key] = None
        timeout = data["connection_timeout"]
        if not isinstance(timeout, int | float) or not (1 <= timeout <= 120):
            data["connection_timeout"] = defaults["connection_timeout"]
        host = data["web_bind_host"]
        if not isinstance(host, str) or not host.strip():
            data["web_bind_host"] = defaults["web_bind_host"]
        return Settings(**data)


def _migrate(data: dict[str, Any]) -> dict[str, Any]:
    """Upgrade an on-disk settings dict to the current schema version.

    No migrations exist yet — schema version 1 is the first shipped
    shape. Future versions add ``if version < N: ...`` steps here.
    """
    data.setdefault("schema_version", 0)
    data["schema_version"] = SCHEMA_VERSION
    return data


def _quarantine_corrupted(path: Path) -> None:
    """Move an unreadable settings file aside rather than silently deleting it."""
    with contextlib.suppress(OSError):
        path.rename(path.with_name(f"settings.corrupted-{int(time.time())}.json"))


def load() -> Settings:
    """Load settings from disk, falling back to defaults if missing/corrupt."""
    path = settings_path()
    if not path.exists():
        return Settings()

    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            raise ValueError("settings file must contain a JSON object")
    except (json.JSONDecodeError, ValueError, OSError) as exc:
        logger.warning("Settings file %s is corrupted (%s); restoring defaults", path, exc)
        _quarantine_corrupted(path)
        return Settings()

    raw = _migrate(raw)
    known_fields = {f.name for f in fields(Settings)}
    filtered = {key: value for key, value in raw.items() if key in known_fields}
    try:
        settings = Settings(**filtered)
    except TypeError as exc:
        logger.warning("Settings file %s has an invalid shape (%s); restoring defaults", path, exc)
        _quarantine_corrupted(path)
        return Settings()
    return settings.validated()


def save(settings: Settings) -> None:
    """Persist *settings* atomically (write to a temp file, then rename)."""
    path = settings_path()
    data = asdict(settings.validated())
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(path)

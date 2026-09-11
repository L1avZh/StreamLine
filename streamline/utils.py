"""Utility functions for the StreamLine chat application."""

from __future__ import annotations

import hmac
import json
import logging
import re
import socket
import ssl
from collections.abc import Callable
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.logging import RichHandler

from .paths import log_file_path
from .protocol import MAX_NICKNAME_LENGTH, MIN_NICKNAME_LENGTH

console = Console()

# Strips ANSI/VT100 escape sequences and other C0 control characters
# (except the printable range) from untrusted text before it is ever
# written to a terminal or broadcast to other clients. Without this a
# malicious peer could send escape sequences to move the cursor, hide
# text, or otherwise manipulate another user's terminal ("terminal
# injection").
_CONTROL_CHARS_RE = re.compile(
    r"\x1b\[[0-?]*[ -/]*[@-~]"  # CSI sequences (colors, cursor moves, ...)
    r"|\x1b\][^\x07]*\x07"  # OSC sequences terminated by BEL
    r"|[\x00-\x08\x0b-\x1f\x7f]"  # remaining C0 control characters
)

_NICKNAME_RE = re.compile(r"^[A-Za-z0-9_.\-]+$")


def sanitize_text(text: str) -> str:
    """Strip ANSI escape sequences and control characters from *text*.

    Applied to every piece of untrusted, user-supplied text before it is
    printed to a terminal or relayed to other clients.
    """
    return _CONTROL_CHARS_RE.sub("", text).strip()


def validate_nickname(nickname: str) -> str | None:
    """Return *nickname* if it is well-formed, otherwise ``None``.

    A valid nickname is 1-32 characters of letters, digits, underscore,
    dot, or hyphen. This keeps nicknames safe to embed directly in
    protocol lines and terminal output without further escaping.
    """
    nickname = nickname.strip()
    if not (MIN_NICKNAME_LENGTH <= len(nickname) <= MAX_NICKNAME_LENGTH):
        return None
    if not _NICKNAME_RE.match(nickname):
        return None
    return nickname


def constant_time_equals(a: str, b: str) -> bool:
    """Compare two secrets in constant time to avoid timing attacks."""
    return hmac.compare_digest(a.encode("utf-8"), b.encode("utf-8"))


def _open_rotating_file_handler(resolve_path: Callable[[], Path]) -> RotatingFileHandler | None:
    """Try to open a rotating log file. Returns ``None`` on any OS-level failure.

    *resolve_path* is a callable rather than a plain path because resolving
    the real per-user log path can itself fail (creating the directory), and
    that needs to be inside this same try/except.
    """
    try:
        path = resolve_path()
        return RotatingFileHandler(path, maxBytes=1_000_000, backupCount=3, encoding="utf-8")
    except OSError:
        return None


def setup_logging(debug: bool = False) -> None:
    """Configure logging for a polished, non-technical console experience.

    Full diagnostic logs (every connection, join/leave, etc.) normally go to
    the per-user log file (see :mod:`streamline.paths`) so a problem can be
    investigated after the fact. The console only shows warnings and errors
    by default — the curated ``console.print`` messages elsewhere are the
    actual UI — unless *debug* is set, which raises the console to match.

    If the per-user log location isn't writable (locked-down permissions,
    a read-only filesystem, ...) this falls back to the system temp
    directory, and finally to console-only logging, rather than crashing
    every single command over something that isn't fatal to using the app.
    """
    handlers: list[logging.Handler] = []

    file_handler = _open_rotating_file_handler(log_file_path)
    if file_handler is None:
        import tempfile

        file_handler = _open_rotating_file_handler(
            lambda: Path(tempfile.gettempdir()) / "streamline.log"
        )
    if file_handler is not None:
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)-8s %(name)s: %(message)s")
        )
        handlers.append(file_handler)

    console_handler = RichHandler(
        rich_tracebacks=debug, show_path=debug, console=console, markup=False
    )
    console_handler.setLevel(logging.DEBUG if debug else logging.WARNING)
    handlers.append(console_handler)

    logging.basicConfig(level=logging.DEBUG, format="%(message)s", handlers=handlers, force=True)
    if file_handler is None:
        logging.getLogger(__name__).warning(
            "Could not open a log file (no writable location found); logging to console only."
        )


def print_banner() -> None:
    """Print a colorful ASCII banner using Rich."""
    banner = r"""
 ___ _                      _    _
/ __| |_ _ _ ___ __ _ _ __ | |  (_)_ _  ___
\__ \  _| '_/ -_) _` | '  \| |__| | ' \/ -_)
|___/\__|_| \___\__,_|_|_|_|____|_|_||_\___|
    """
    console.print(banner, style="bold cyan")
    console.print("         - Modern StreamLine\n", style="magenta")


def load_config(path: str | Path) -> dict[str, Any]:
    """Load configuration from *path*.

    Returns the parsed configuration, or an empty dict if the file is
    missing or invalid. Callers should not treat an empty dict as an
    error; ``load_config`` never raises for these expected conditions.
    """
    try:
        with open(path, encoding="utf-8") as fh:
            config = json.load(fh)
    except FileNotFoundError:
        logging.getLogger(__name__).warning("Config file %s not found", path)
        return {}
    except json.JSONDecodeError as exc:
        logging.getLogger(__name__).error("Invalid JSON in %s: %s", path, exc)
        return {}
    if not isinstance(config, dict):
        logging.getLogger(__name__).error(
            "Config file %s must contain a JSON object, got %s", path, type(config).__name__
        )
        return {}
    logging.getLogger(__name__).debug("Config loaded %s", config)
    return config


def get_config_value(config: dict[str, Any], key: str, default: Any = None) -> Any:
    """Retrieve *key* from *config* or return *default*."""
    value = config.get(key, default)
    if value is None:
        return default
    return value


def find_free_port() -> int:
    """Return a free TCP port assigned by the OS."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        port: int = s.getsockname()[1]
        return port


def create_ssl_context(certfile: str | None, keyfile: str | None) -> ssl.SSLContext | None:
    """Create a server-side SSL context if *certfile* and *keyfile* are provided."""
    if not (certfile and keyfile):
        return None
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    context.load_cert_chain(certfile=certfile, keyfile=keyfile)
    return context


def create_client_ssl_context(cafile: str | None) -> ssl.SSLContext:
    """Return a client SSL context, verifying the server certificate.

    If *cafile* is omitted, the system's default trust store is used.
    """
    context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH, cafile=cafile)
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    return context

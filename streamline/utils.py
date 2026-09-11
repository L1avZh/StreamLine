"""Utility functions for the StreamLine chat application."""

from __future__ import annotations

import hmac
import json
import logging
import re
import socket
import ssl
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.logging import RichHandler

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


def setup_logging(level: int = logging.INFO) -> None:
    """Configure logging to use Rich's handler."""
    logging.basicConfig(
        level=level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(rich_tracebacks=True, console=console)],
        force=True,
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

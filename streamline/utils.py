"""Utility functions for StreamLine chat application."""
from __future__ import annotations

import json
import logging
import socket
import ssl
from pathlib import Path
from typing import Any, Dict, Optional

from rich.console import Console
from rich.logging import RichHandler

console = Console()


def setup_logging(level: int = logging.INFO) -> None:
    """Configure logging to use Rich's handler."""
    logging.basicConfig(
        level=level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(rich_tracebacks=True, console=console)],
    )


def print_banner() -> None:
    """Print a colorful ASCII banner using Rich."""
    banner = r"""
 ___ _                      _    _          
/ __| |_ _ _ ___ __ _ _ __ | |  (_)_ _  ___ \\
\__ \  _| '_/ -_) _` | '  \\| |__| | ' \\/ -_)
|___/\__|_| \___\__,_|_|_|_|____|_|_||_\___|
    """
    console.print(banner, style="bold cyan")
    console.print("         - Modern StreamLine\n", style="magenta")


def load_config(path: str | Path) -> Dict[str, Any]:
    """Load configuration from *path*.

    Parameters
    ----------
    path: Path-like
        Location of a JSON configuration file.

    Returns
    -------
    dict
        Parsed configuration or empty dict if loading fails.
    """
    try:
        with open(path, "r", encoding="utf-8") as fh:
            config = json.load(fh)
            logging.getLogger(__name__).debug("Config loaded %s", config)
            return config
    except FileNotFoundError:
        logging.getLogger(__name__).warning("Config file %s not found", path)
    except json.JSONDecodeError as exc:
        logging.getLogger(__name__).error("Invalid JSON in %s: %s", path, exc)
    return {}


def get_config_value(config: Dict[str, Any], key: str, default: Any = None) -> Any:
    """Retrieve *key* from *config* or return *default*."""
    value = config.get(key, default)
    if value is None:
        logging.getLogger(__name__).warning("Config key '%s' missing; using default %r", key, default)
        return default
    return value


def find_free_port() -> int:
    """Return a free TCP port assigned by the OS."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]


def create_ssl_context(certfile: Optional[str], keyfile: Optional[str]) -> Optional[ssl.SSLContext]:
    """Create an SSL context if *certfile* and *keyfile* are provided."""
    if certfile and keyfile:
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(certfile=certfile, keyfile=keyfile)
        return context
    return None


def create_client_ssl_context(cafile: Optional[str]) -> ssl.SSLContext:
    """Return an SSL context for clients verifying server certificate if *cafile* provided."""
    context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH, cafile=cafile)
    return context

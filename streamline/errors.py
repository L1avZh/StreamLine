"""Translates low-level connection exceptions into messages a user can act on.

Used by both the terminal client and the web interface so a dropped
connection reads the same, plain-English way everywhere — never a raw
Python traceback. Full exception details still go to the log file (see
:func:`streamline.utils.setup_logging`) for anyone who needs them.
"""

from __future__ import annotations

import socket
import ssl


def describe_connection_error(exc: Exception, host: str, port: int) -> str:
    """Return a short, human-readable explanation of a failed connection."""
    if isinstance(exc, socket.gaierror):
        return f"Could not resolve the address '{host}'. Check for typos."
    if isinstance(exc, ConnectionRefusedError):
        return (
            f"Could not connect to {host}:{port} — connection refused. "
            "The server is probably offline, or the port is wrong."
        )
    if isinstance(exc, TimeoutError):
        return (
            f"Could not connect to {host}:{port} — timed out. "
            "Check the address, or that a firewall isn't blocking it."
        )
    if isinstance(exc, ssl.SSLCertVerificationError):
        return (
            f"Could not verify {host}:{port}'s TLS certificate. "
            "If this is a self-signed certificate, supply its CA file."
        )
    if isinstance(exc, ssl.SSLError):
        return f"TLS/security handshake with {host}:{port} failed: {exc.reason or exc}"
    if isinstance(exc, OSError) and exc.strerror:
        return f"Could not connect to {host}:{port} ({exc.strerror})."
    return f"Could not connect to {host}:{port}: {exc}"

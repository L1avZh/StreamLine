"""Guards against a malicious web page driving the local StreamLine server.

Because the web interface binds to localhost, the browser's usual
same-origin protections are the only thing standing between "a page the
user has open in another tab" and "this machine's chat server" — a
browser will happily let JavaScript on `evil.example` open a WebSocket or
POST to `http://127.0.0.1:8765` (cross-site WebSocket hijacking). We can't
rely on CORS for WebSocket upgrades, so every state-changing or
interactive endpoint checks the ``Origin`` header itself: a request with
no Origin (curl, tests, same-origin fetches some browsers omit it for) is
allowed, but a *present* Origin must point at localhost.
"""

from __future__ import annotations

from urllib.parse import urlsplit

_LOCAL_HOSTS = {"127.0.0.1", "localhost", "::1", "[::1]"}


def is_local_origin(origin: str | None) -> bool:
    """True if *origin* is absent or points at this machine."""
    if not origin:
        return True
    hostname = urlsplit(origin).hostname
    return hostname in _LOCAL_HOSTS

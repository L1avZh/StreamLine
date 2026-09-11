"""Starts the StreamLine web interface: one call, nothing to run by hand."""

from __future__ import annotations

import asyncio
import contextlib
import socket
import webbrowser

import uvicorn

from ..utils import console
from .app import create_app

#: Preferred port for the web interface. If it's taken, the OS picks a free
#: one instead — the user never has to know or care which port is used.
DEFAULT_PORT = 8765

# How long to wait for uvicorn to finish binding before we consider the
# server "ready" (and safe to open a browser against).
_READY_POLL_INTERVAL = 0.05
_READY_TIMEOUT = 10.0


def resolve_port(host: str, preferred: int) -> int:
    """Return *preferred* if free, otherwise an OS-assigned free port."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            probe.bind((host, preferred))
            return preferred
        except OSError:
            probe.bind((host, 0))
            port: int = probe.getsockname()[1]
            return port


async def _serve(host: str, port: int, open_browser: bool) -> None:
    console.print("Starting StreamLine Web Interface...\n")
    console.print("[green]✓[/green] Preparing application")

    app = create_app()
    config = uvicorn.Config(app, host=host, port=port, log_level="warning", access_log=False)
    server = uvicorn.Server(config)

    console.print("[green]✓[/green] Starting local server")
    serve_task = asyncio.create_task(server.serve())

    waited = 0.0
    while not server.started and not serve_task.done() and waited < _READY_TIMEOUT:
        await asyncio.sleep(_READY_POLL_INTERVAL)
        waited += _READY_POLL_INTERVAL

    if serve_task.done():
        # Surfaces bind failures (e.g. permission denied on the port) instead
        # of silently hanging.
        serve_task.result()
        return

    url = f"http://{host}:{port}"
    console.print("[green]✓[/green] Web interface ready\n")
    console.print(f"Open: [bold cyan]{url}[/bold cyan]\n")
    if open_browser:
        console.print("Your browser will open automatically.")
        webbrowser.open(url)
    console.print("Press Ctrl+C to stop StreamLine.\n", style="dim")

    try:
        await serve_task
    finally:
        with contextlib.suppress(asyncio.CancelledError):
            await serve_task


def run_web(host: str = "127.0.0.1", port: int = DEFAULT_PORT, open_browser: bool = True) -> None:
    """Start the local web interface. Blocks until interrupted (Ctrl+C)."""
    resolved_port = resolve_port(host, port)
    with contextlib.suppress(KeyboardInterrupt):
        asyncio.run(_serve(host, resolved_port, open_browser))
    console.print("\nStreamLine web interface stopped.", style="red")

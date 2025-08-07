"""Command line interface for StreamLine using Click."""
from __future__ import annotations

import asyncio
import click

from .client import run_client
from .server import run_server
from .utils import (
    print_banner,
    setup_logging,
    find_free_port,
    create_ssl_context,
    create_client_ssl_context,
    console,
)


@click.group()
def cli() -> None:
    """StreamLine chat application."""
    setup_logging()


@cli.command()
@click.option("--host", default="0.0.0.0", show_default=True, help="Host to bind")
@click.option("--port", type=int, default=None, help="Port to bind")
@click.option("--password", default=None, help="Pre-shared password for clients")
@click.option("--certfile", type=click.Path(exists=True), default=None, help="TLS certificate file")
@click.option("--keyfile", type=click.Path(exists=True), default=None, help="TLS private key file")
def server(host: str, port: int | None, password: str | None, certfile: str | None, keyfile: str | None) -> None:
    """Run the StreamLine server."""
    print_banner()
    port = port or find_free_port()
    ssl_context = create_ssl_context(certfile, keyfile)
    console.print(f"Starting server on {host}:{port}")
    asyncio.run(run_server(host, port, password, ssl_context))


@cli.command()
@click.option("--host", default="127.0.0.1", show_default=True, help="Server host")
@click.option("--port", type=int, default=12345, show_default=True, help="Server port")
@click.option("--nickname", prompt=True, help="Nickname to use")
@click.option("--password", default=None, help="Server password if required")
@click.option("--cafile", type=click.Path(exists=True), default=None, help="CA file for TLS validation")
@click.option("--use-ssl", is_flag=True, default=False, help="Enable TLS")
def client(host: str, port: int, nickname: str, password: str | None, cafile: str | None, use_ssl: bool) -> None:
    """Run the StreamLine client."""
    print_banner()
    ssl_ctx = create_client_ssl_context(cafile) if use_ssl else None
    asyncio.run(run_client(host, port, nickname, password, ssl_ctx))


if __name__ == "__main__":
    cli()

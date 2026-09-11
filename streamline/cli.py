"""Command line interface for StreamLine using Click."""

from __future__ import annotations

import asyncio

import click

from . import __version__
from .client import run_client
from .server import run_server
from .utils import (
    console,
    create_client_ssl_context,
    create_ssl_context,
    find_free_port,
    get_config_value,
    load_config,
    print_banner,
    setup_logging,
)


@click.group()
@click.version_option(__version__, prog_name="streamline")
def cli() -> None:
    """StreamLine chat application."""
    setup_logging()


@cli.command()
@click.option("--host", default="0.0.0.0", show_default=True, help="Host to bind")
@click.option("--port", type=int, default=None, help="Port to bind (random free port if omitted)")
@click.option("--password", default=None, help="Pre-shared password clients must supply")
@click.option("--certfile", type=click.Path(exists=True), default=None, help="TLS certificate file")
@click.option("--keyfile", type=click.Path(exists=True), default=None, help="TLS private key file")
@click.option(
    "--max-clients", type=int, default=200, show_default=True, help="Maximum simultaneous clients"
)
@click.option(
    "--config", type=click.Path(exists=True), default=None, help="Path to JSON config file"
)
def server(
    host: str,
    port: int | None,
    password: str | None,
    certfile: str | None,
    keyfile: str | None,
    max_clients: int,
    config: str | None,
) -> None:
    """Run the StreamLine server."""
    print_banner()
    cfg = load_config(config) if config else {}
    host = get_config_value(cfg, "host", host)
    port = port or get_config_value(cfg, "server_port", find_free_port())
    password = password or get_config_value(cfg, "server_password")
    if bool(certfile) != bool(keyfile):
        raise click.UsageError("--certfile and --keyfile must be provided together")
    ssl_context = create_ssl_context(certfile, keyfile)
    console.print(f"Starting server on {host}:{port}")
    if password is None:
        console.print(
            "Warning: no password configured. Anyone who can reach this port can join.",
            style="yellow",
        )
    if ssl_context is None:
        console.print(
            "Warning: TLS is disabled. Traffic (including any password) is sent in plaintext.",
            style="yellow",
        )
    asyncio.run(run_server(host, port, password, ssl_context, max_clients))


@cli.command()
@click.option("--host", default="127.0.0.1", show_default=True, help="Server host")
@click.option("--port", type=int, default=12345, show_default=True, help="Server port")
@click.option("--nickname", prompt=True, help="Nickname to use")
@click.option("--password", default=None, help="Server password if required")
@click.option(
    "--cafile", type=click.Path(exists=True), default=None, help="CA file for TLS validation"
)
@click.option("--use-ssl", is_flag=True, default=False, help="Enable TLS")
@click.option(
    "--config", type=click.Path(exists=True), default=None, help="Path to JSON config file"
)
def client(
    host: str,
    port: int,
    nickname: str,
    password: str | None,
    cafile: str | None,
    use_ssl: bool,
    config: str | None,
) -> None:
    """Run the StreamLine client."""
    print_banner()
    cfg = load_config(config) if config else {}
    host = get_config_value(cfg, "host", host)
    port = get_config_value(cfg, "port", port)
    nickname = get_config_value(cfg, "nickname", nickname)
    password = password or get_config_value(cfg, "password")
    ssl_ctx = create_client_ssl_context(cafile) if use_ssl else None
    asyncio.run(run_client(host, port, nickname, password, ssl_ctx))


if __name__ == "__main__":
    cli()

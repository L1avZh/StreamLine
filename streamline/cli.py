"""Command line interface for StreamLine using Click.

``streamline`` with no arguments drops into an interactive menu so a new
user never has to learn a command up front. ``streamline server`` /
``streamline client`` / ``streamline web`` remain available directly for
scripting and for anyone who already knows what they want.
"""

from __future__ import annotations

import asyncio

import click
from rich.panel import Panel
from rich.prompt import IntPrompt, Prompt

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


@click.group(invoke_without_command=True, no_args_is_help=False)
@click.version_option(__version__, prog_name="streamline")
@click.pass_context
def cli(ctx: click.Context) -> None:
    """StreamLine chat application.

    Run with no arguments for an interactive menu, or use a subcommand
    (`server`, `client`, `web`) directly.
    """
    setup_logging()
    if ctx.invoked_subcommand is None:
        _interactive_start()


def _interactive_start() -> None:
    print_banner()
    console.print(
        Panel(
            "[bold]Choose how you want to continue:[/bold]\n\n"
            "  [cyan]1[/cyan]  Command Line Interface\n"
            "  [cyan]2[/cyan]  Web Interface",
            title="StreamLine",
            border_style="cyan",
            width=44,
        )
    )
    choice = Prompt.ask("Select an option", choices=["1", "2"], default="1", show_choices=False)
    console.print()
    if choice == "1":
        _guided_cli()
    else:
        _start_web(host="127.0.0.1", port=None, open_browser=True)


def _guided_cli() -> None:
    role = Prompt.ask(
        "Do you want to [bold]host[/bold] a chat or [bold]join[/bold] one?",
        choices=["host", "join"],
        default="host",
    )
    console.print()
    if role == "host":
        host = Prompt.ask("Bind address", default="0.0.0.0")
        port_raw = Prompt.ask("Port [dim](leave blank for automatic)[/dim]", default="")
        password = Prompt.ask("Password [dim](leave blank for none)[/dim]", default="") or None
        port = int(port_raw) if port_raw else find_free_port()
        console.print(f"\nStarting server on {host}:{port}")
        if password is None:
            console.print(
                "Warning: no password configured. Anyone who can reach this port can join.",
                style="yellow",
            )
        asyncio.run(run_server(host, port, password, None, 200))
    else:
        host = Prompt.ask("Server host", default="127.0.0.1")
        port = IntPrompt.ask("Server port")
        nickname = Prompt.ask("Nickname")
        password = Prompt.ask("Password [dim](leave blank if none)[/dim]", default="") or None
        asyncio.run(run_client(host, port, nickname, password, None))


def _start_web(host: str, port: int | None, open_browser: bool) -> None:
    from .web import run_web
    from .web.launcher import DEFAULT_PORT

    run_web(host=host, port=port or DEFAULT_PORT, open_browser=open_browser)


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
    """Run the StreamLine server directly (no menu)."""
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
    """Run the StreamLine client directly (no menu)."""
    print_banner()
    cfg = load_config(config) if config else {}
    host = get_config_value(cfg, "host", host)
    port = get_config_value(cfg, "port", port)
    nickname = get_config_value(cfg, "nickname", nickname)
    password = password or get_config_value(cfg, "password")
    ssl_ctx = create_client_ssl_context(cafile) if use_ssl else None
    asyncio.run(run_client(host, port, nickname, password, ssl_ctx))


@cli.command()
@click.option(
    "--host",
    default="127.0.0.1",
    show_default=True,
    help="Interface to bind. Keep this local unless you intend to expose the web UI.",
)
@click.option("--port", type=int, default=None, help="Port to use (default: 8765, or next free)")
@click.option(
    "--no-browser", is_flag=True, default=False, help="Don't open a browser automatically"
)
def web(host: str, port: int | None, no_browser: bool) -> None:
    """Start the StreamLine web interface directly (no menu)."""
    _start_web(host=host, port=port, open_browser=not no_browser)


if __name__ == "__main__":
    cli()

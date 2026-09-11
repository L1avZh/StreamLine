"""Command line interface for StreamLine using Click.

``streamline`` with no arguments is the front door: first-run setup, then
a polished menu (Web / CLI / Settings / Help / Exit). Power users keep
direct access via `server` / `client` / `web` / `settings` subcommands —
none of this menu logic gets in their way.
"""

from __future__ import annotations

import asyncio
import contextlib
import dataclasses
import sys
from typing import Any, cast, get_args

import click
from rich.panel import Panel
from rich.prompt import Confirm, IntPrompt, Prompt

from . import __version__
from . import settings as settings_store
from .client import run_client
from .server import run_server
from .settings import Interface, LogLevel, Settings
from .utils import (
    console,
    create_client_ssl_context,
    create_ssl_context,
    find_free_port,
    get_config_value,
    load_config,
    print_banner,
    setup_logging,
    validate_nickname,
)


def _ensure_line_buffered_output() -> None:
    """Flush output promptly even when redirected to a file.

    Without this, output sits in a full buffer for a long time when
    stdout isn't a terminal (e.g. ``streamline web > out.log``), which
    looks like the app has hung when it hasn't.
    """
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            with contextlib.suppress(Exception):
                reconfigure(line_buffering=True)


@click.group(invoke_without_command=True, no_args_is_help=False)
@click.version_option(__version__, prog_name="streamline")
@click.option(
    "--debug",
    is_flag=True,
    envvar="STREAMLINE_DEBUG",
    help="Show detailed diagnostic logging on the console (always written to the log file).",
)
@click.pass_context
def cli(ctx: click.Context, debug: bool) -> None:
    """StreamLine chat application.

    Run with no arguments for the main menu, or use a subcommand
    (`server`, `client`, `web`, `settings`) directly.
    """
    _ensure_line_buffered_output()
    setup_logging(debug=debug)
    if ctx.invoked_subcommand is None:
        _launch_menu()


def _launch_menu() -> None:
    current = settings_store.load()
    print_banner()
    if not current.first_run_complete:
        current = _first_run_wizard(current)

    if current.default_interface == "cli":
        _guided_cli(current)
        return
    if current.default_interface == "web":
        _start_web(host="127.0.0.1", port=current.web_port, open_browser=current.web_open_browser)
        return
    _main_menu(current)


def _first_run_wizard(current: Settings) -> Settings:
    console.print(
        Panel(
            "[bold]Welcome to StreamLine[/bold]\n\n"
            "A private, self-hosted chat — no account, no server to trust.\n"
            "Two quick questions and you're set.",
            border_style="cyan",
            width=56,
        )
    )
    interface = cast(
        Interface,
        Prompt.ask(
            "How would you like to use StreamLine by default?",
            choices=list(get_args(Interface)),
            default="web",
        ),
    )
    nickname_raw = Prompt.ask("Nickname", default=current.nickname)
    nickname = validate_nickname(nickname_raw) or current.nickname
    updated = dataclasses.replace(
        current, default_interface=interface, nickname=nickname, first_run_complete=True
    )
    _save_settings_or_warn(updated)
    console.print("\nDone — you can change this anytime from [bold]Settings[/bold].\n", style="dim")
    return updated


def _save_settings_or_warn(current: Settings) -> bool:
    """Save settings; on failure (e.g. a read-only config directory), warn
    instead of crashing — the user can keep using this session either way."""
    try:
        settings_store.save(current)
        return True
    except OSError as exc:
        console.print(f"Warning: could not save settings ({exc}).", style="yellow")
        return False


def _main_menu(current: Settings) -> None:
    options = {"1", "2", "3", "4", "5"}
    while True:
        console.print(
            Panel(
                "[dim]Private. Simple. Connected.[/dim]\n\n"
                "  [cyan]1[/cyan]  Web Interface\n"
                "  [cyan]2[/cyan]  Command Line\n"
                "  [cyan]3[/cyan]  Settings\n"
                "  [cyan]4[/cyan]  Help\n"
                "  [cyan]5[/cyan]  Exit",
                title="StreamLine",
                border_style="cyan",
                width=44,
            )
        )
        choice = Prompt.ask(
            "Select an option", choices=sorted(options), default="1", show_choices=False
        )
        console.print()
        if choice == "1":
            _start_web(
                host="127.0.0.1", port=current.web_port, open_browser=current.web_open_browser
            )
            return
        if choice == "2":
            _guided_cli(current)
            return
        if choice == "3":
            current = _settings_menu(current)
            continue
        if choice == "4":
            _print_help()
            continue
        return  # Exit


def _settings_menu(current: Settings) -> Settings:
    while True:
        console.print(
            Panel(
                f"  Nickname            {current.nickname}\n"
                f"  Default interface   {current.default_interface}\n"
                f"  Web port            {current.web_port or 'automatic'}\n"
                f"  Open browser        {'yes' if current.web_open_browser else 'no'}\n"
                f"  Debug logging       {'on' if current.log_level == 'debug' else 'off'}",
                title="Settings",
                border_style="cyan",
                width=48,
            )
        )
        console.print(
            "  [cyan]1[/cyan] Nickname          [cyan]2[/cyan] Default interface\n"
            "  [cyan]3[/cyan] Web port          [cyan]4[/cyan] Auto-open browser\n"
            "  [cyan]5[/cyan] Debug logging     [cyan]6[/cyan] Reset to defaults\n"
            "  [cyan]0[/cyan] Back"
        )
        choice = Prompt.ask(
            "\nSelect an option",
            choices=[str(i) for i in range(7)],
            default="0",
            show_choices=False,
        )
        console.print()
        if choice == "0":
            return current
        if choice == "1":
            nickname = Prompt.ask("Nickname", default=current.nickname)
            valid = validate_nickname(nickname)
            if valid is None:
                console.print(
                    "Nickname must be 1-32 characters: letters, numbers, _ . -", style="red"
                )
                continue
            current = dataclasses.replace(current, nickname=valid)
        elif choice == "2":
            value = cast(
                Interface,
                Prompt.ask(
                    "Default interface",
                    choices=list(get_args(Interface)),
                    default=current.default_interface,
                ),
            )
            current = dataclasses.replace(current, default_interface=value)
        elif choice == "3":
            raw = Prompt.ask("Web port (blank = automatic)", default=str(current.web_port or ""))
            try:
                port = int(raw) if raw.strip() else None
            except ValueError:
                console.print("Port must be a number.", style="red")
                continue
            current = dataclasses.replace(current, web_port=port)
        elif choice == "4":
            current = dataclasses.replace(current, web_open_browser=not current.web_open_browser)
        elif choice == "5":
            new_level: LogLevel = "normal" if current.log_level == "debug" else "debug"
            current = dataclasses.replace(current, log_level=new_level)
        elif choice == "6":
            if Confirm.ask("Reset all settings to defaults?", default=False):
                current = Settings(first_run_complete=True)
        if _save_settings_or_warn(current):
            console.print("Saved.\n", style="green")


def _print_help() -> None:
    console.print(
        Panel(
            "StreamLine is a private, self-hosted chat app — your machine, your rules.\n\n"
            "  [bold]Web Interface[/bold]   Host or join a chat from your browser.\n"
            "  [bold]Command Line[/bold]    Host or join a chat from the terminal.\n\n"
            "Advanced usage:\n"
            "  streamline server --help\n"
            "  streamline client --help\n"
            "  streamline web --help\n"
            "  streamline settings --help\n\n"
            f"Version {__version__}  ·  https://github.com/L1avZh/StreamLine",
            title="Help",
            border_style="cyan",
            width=60,
        )
    )
    console.print()


def _guided_cli(current: Settings) -> None:
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
        host = Prompt.ask("Server host", default=current.default_host)
        port = (
            IntPrompt.ask("Server port", default=current.default_port)
            if current.default_port
            else IntPrompt.ask("Server port")
        )
        nickname = Prompt.ask("Nickname", default=current.nickname)
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


_SETTINGS_BOOL_FIELDS = {"web_open_browser", "first_run_complete"}
_SETTINGS_INT_OR_NONE_FIELDS = {"default_port", "web_port"}
_SETTINGS_FLOAT_FIELDS = {"connection_timeout"}


def _coerce_setting(key: str, raw: str) -> Any:
    if key in _SETTINGS_BOOL_FIELDS:
        return raw.strip().lower() in {"1", "true", "yes", "on"}
    if key in _SETTINGS_INT_OR_NONE_FIELDS:
        return int(raw) if raw.strip() else None
    if key in _SETTINGS_FLOAT_FIELDS:
        return float(raw)
    return raw


@cli.group(name="settings")
def settings_group() -> None:
    """View or change StreamLine's persisted settings."""


@settings_group.command("show")
def settings_show() -> None:
    """Print all current settings."""
    current = settings_store.load()
    for field in dataclasses.fields(current):
        if field.name == "schema_version":
            continue
        console.print(f"[bold]{field.name}[/bold] = {getattr(current, field.name)}")


@settings_group.command("set")
@click.argument("key")
@click.argument("value")
def settings_set(key: str, value: str) -> None:
    """Set one setting, e.g. `streamline settings set nickname alice`."""
    current = settings_store.load()
    known_fields = {f.name for f in dataclasses.fields(current)}
    if key not in known_fields or key == "schema_version":
        raise click.UsageError(
            f"Unknown setting '{key}'. Run 'streamline settings show' to see valid keys."
        )
    try:
        coerced = _coerce_setting(key, value)
    except ValueError as exc:
        raise click.UsageError(f"Invalid value for '{key}': {exc}") from exc
    if key == "nickname" and validate_nickname(str(coerced)) is None:
        raise click.UsageError("Nickname must be 1-32 characters: letters, numbers, _ . -")

    updated = dataclasses.replace(current, **{key: coerced}).validated()
    try:
        settings_store.save(updated)
    except OSError as exc:
        raise click.ClickException(f"Could not save settings: {exc}") from exc
    console.print(f"{key} = {getattr(updated, key)}", style="green")


@settings_group.command("reset")
def settings_reset() -> None:
    """Reset all settings to their defaults."""
    try:
        settings_store.save(Settings(first_run_complete=True))
    except OSError as exc:
        raise click.ClickException(f"Could not save settings: {exc}") from exc
    console.print("Settings reset to defaults.", style="green")


if __name__ == "__main__":
    cli()

from __future__ import annotations

from click.testing import CliRunner

from streamline import cli as cli_module
from streamline.cli import cli


def test_cli_help():
    result = CliRunner().invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "StreamLine chat application" in result.output
    assert "interactive menu" in result.output


def test_cli_version():
    result = CliRunner().invoke(cli, ["--version"])
    assert result.exit_code == 0


def test_cli_lists_web_command():
    result = CliRunner().invoke(cli, ["--help"])
    assert "web" in result.output
    assert "server" in result.output
    assert "client" in result.output


def test_web_help():
    result = CliRunner().invoke(cli, ["web", "--help"])
    assert result.exit_code == 0
    assert "web interface" in result.output.lower()


def test_server_requires_certfile_and_keyfile_together():
    result = CliRunner().invoke(cli, ["server", "--certfile", "/dev/null"])
    assert result.exit_code != 0
    assert "--certfile and --keyfile" in result.output


def test_interactive_start_dispatches_to_guided_cli(monkeypatch):
    calls = []
    monkeypatch.setattr(cli_module, "_guided_cli", lambda: calls.append("cli"))
    monkeypatch.setattr(cli_module, "_start_web", lambda **kw: calls.append(("web", kw)))
    monkeypatch.setattr(cli_module.Prompt, "ask", staticmethod(lambda *a, **k: "1"))

    cli_module._interactive_start()

    assert calls == ["cli"]


def test_interactive_start_dispatches_to_web(monkeypatch):
    calls = []
    monkeypatch.setattr(cli_module, "_guided_cli", lambda: calls.append("cli"))
    monkeypatch.setattr(cli_module, "_start_web", lambda **kw: calls.append(("web", kw)))
    monkeypatch.setattr(cli_module.Prompt, "ask", staticmethod(lambda *a, **k: "2"))

    cli_module._interactive_start()

    assert len(calls) == 1 and calls[0][0] == "web"


def test_guided_cli_host_path_calls_run_server(monkeypatch):
    captured = {}

    async def fake_run_server(host, port, password, ssl_context, max_clients):
        captured.update(host=host, port=port, password=password, max_clients=max_clients)

    prompts = iter(["host", "127.0.0.1", "9999", ""])
    monkeypatch.setattr(cli_module, "run_server", fake_run_server)
    monkeypatch.setattr(cli_module.Prompt, "ask", staticmethod(lambda *a, **k: next(prompts)))

    cli_module._guided_cli()

    assert captured == {"host": "127.0.0.1", "port": 9999, "password": None, "max_clients": 200}

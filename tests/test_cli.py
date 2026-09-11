from __future__ import annotations

from click.testing import CliRunner

from streamline import cli as cli_module
from streamline import settings as settings_store
from streamline.cli import cli
from streamline.settings import Settings


def test_cli_help():
    result = CliRunner().invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "StreamLine chat application" in result.output
    assert "main menu" in result.output


def test_cli_version():
    result = CliRunner().invoke(cli, ["--version"])
    assert result.exit_code == 0


def test_cli_lists_all_commands():
    result = CliRunner().invoke(cli, ["--help"])
    for name in ("web", "server", "client", "settings"):
        assert name in result.output


def test_web_help():
    result = CliRunner().invoke(cli, ["web", "--help"])
    assert result.exit_code == 0
    assert "web interface" in result.output.lower()


def test_server_requires_certfile_and_keyfile_together():
    result = CliRunner().invoke(cli, ["server", "--certfile", "/dev/null"])
    assert result.exit_code != 0
    assert "--certfile and --keyfile" in result.output


def test_settings_show():
    settings_store.save(Settings(nickname="alice"))
    result = CliRunner().invoke(cli, ["settings", "show"])
    assert result.exit_code == 0
    assert "nickname = alice" in result.output


def test_settings_set_persists_value():
    result = CliRunner().invoke(cli, ["settings", "set", "nickname", "bob"])
    assert result.exit_code == 0
    assert settings_store.load().nickname == "bob"


def test_settings_set_rejects_unknown_key():
    result = CliRunner().invoke(cli, ["settings", "set", "not_a_real_setting", "x"])
    assert result.exit_code != 0
    assert "Unknown setting" in result.output


def test_settings_set_rejects_invalid_nickname():
    result = CliRunner().invoke(cli, ["settings", "set", "nickname", "not valid!!"])
    assert result.exit_code != 0


def test_settings_set_coerces_bool_field():
    result = CliRunner().invoke(cli, ["settings", "set", "web_open_browser", "false"])
    assert result.exit_code == 0
    assert settings_store.load().web_open_browser is False


def test_settings_reset():
    settings_store.save(Settings(nickname="carol"))
    result = CliRunner().invoke(cli, ["settings", "reset"])
    assert result.exit_code == 0
    assert settings_store.load().nickname == "guest"


def test_main_menu_dispatches_to_guided_cli(monkeypatch):
    calls = []
    monkeypatch.setattr(cli_module, "_guided_cli", lambda current: calls.append("cli"))
    monkeypatch.setattr(cli_module.Prompt, "ask", staticmethod(lambda *a, **k: "2"))

    cli_module._main_menu(Settings())

    assert calls == ["cli"]


def test_main_menu_dispatches_to_web(monkeypatch):
    calls = []
    monkeypatch.setattr(cli_module, "_start_web", lambda **kw: calls.append(("web", kw)))
    monkeypatch.setattr(cli_module.Prompt, "ask", staticmethod(lambda *a, **k: "1"))

    cli_module._main_menu(Settings())

    assert len(calls) == 1 and calls[0][0] == "web"


def test_main_menu_exits_on_choice_five(monkeypatch):
    monkeypatch.setattr(cli_module.Prompt, "ask", staticmethod(lambda *a, **k: "5"))

    cli_module._main_menu(Settings())  # should return without raising or looping forever


def test_first_run_wizard_marks_complete_and_saves(monkeypatch):
    prompts = iter(["cli", "alice"])
    monkeypatch.setattr(cli_module.Prompt, "ask", staticmethod(lambda *a, **k: next(prompts)))

    result = cli_module._first_run_wizard(Settings())

    assert result.first_run_complete is True
    assert result.default_interface == "cli"
    assert result.nickname == "alice"
    assert settings_store.load() == result


def test_guided_cli_host_path_calls_run_server(monkeypatch):
    captured = {}

    async def fake_run_server(host, port, password, ssl_context, max_clients):
        captured.update(host=host, port=port, password=password, max_clients=max_clients)

    prompts = iter(["host", "127.0.0.1", "9999", ""])
    monkeypatch.setattr(cli_module, "run_server", fake_run_server)
    monkeypatch.setattr(cli_module.Prompt, "ask", staticmethod(lambda *a, **k: next(prompts)))

    cli_module._guided_cli(Settings())

    assert captured == {"host": "127.0.0.1", "port": 9999, "password": None, "max_clients": 200}


def test_guided_cli_join_path_uses_settings_defaults(monkeypatch):
    captured = {}

    async def fake_run_client(host, port, nickname, password, ssl_context):
        captured.update(host=host, port=port, nickname=nickname, password=password)

    prompts = iter(["join", "127.0.0.1", "alice", ""])
    monkeypatch.setattr(cli_module, "run_client", fake_run_client)
    monkeypatch.setattr(cli_module.Prompt, "ask", staticmethod(lambda *a, **k: next(prompts)))
    monkeypatch.setattr(cli_module.IntPrompt, "ask", staticmethod(lambda *a, **k: 54140))

    cli_module._guided_cli(Settings(default_host="127.0.0.1"))

    assert captured == {
        "host": "127.0.0.1",
        "port": 54140,
        "nickname": "alice",
        "password": None,
    }

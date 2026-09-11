from __future__ import annotations

from click.testing import CliRunner

from streamline.cli import cli


def test_cli_help():
    result = CliRunner().invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "StreamLine chat application" in result.output


def test_cli_version():
    result = CliRunner().invoke(cli, ["--version"])
    assert result.exit_code == 0


def test_server_requires_certfile_and_keyfile_together():
    result = CliRunner().invoke(cli, ["server", "--certfile", "/dev/null"])
    assert result.exit_code != 0
    assert "--certfile and --keyfile" in result.output

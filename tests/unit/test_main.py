from __future__ import annotations

import runpy
from typing import TYPE_CHECKING

import pytest

from bitbucket_unofficial_cli import __version__
from bitbucket_unofficial_cli import main as main_module
from bitbucket_unofficial_cli.main import default_services
from bitbucket_unofficial_cli.runtime.exit_codes import ExitCode

if TYPE_CHECKING:
    from typer import Typer
    from typer.testing import CliRunner


def test_version_flag_prints_the_version(cli: Typer, runner: CliRunner) -> None:
    # Arrange
    # Act
    result = runner.invoke(cli, ["--version"])
    # Assert
    assert result.exit_code == ExitCode.OK
    assert result.stdout == f"bitbucket {__version__}\n"


def test_no_arguments_prints_the_help(cli: Typer, runner: CliRunner) -> None:
    # Arrange
    # Act
    result = runner.invoke(cli, [])
    # Assert
    assert "Unofficial command-line interface for Bitbucket Cloud" in result.stdout
    for command in ("auth", "config", "user", "workspace", "repo"):
        assert command in result.stdout


def test_default_services_wire_the_real_stores(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pytest.TempPathFactory
) -> None:
    # Arrange
    monkeypatch.setenv("BITBUCKET_CLI_CONFIG_DIR", str(tmp_path))
    # Act
    services = default_services()
    # Assert
    assert services.settings.path == tmp_path / "config.toml"
    assert services.credentials.file.path == tmp_path / "credentials.toml"


def test_run_invokes_the_app(monkeypatch: pytest.MonkeyPatch) -> None:
    # Arrange
    calls: list[str] = []
    monkeypatch.setattr(main_module, "APP", lambda *, prog_name: calls.append(prog_name))
    # Act
    main_module.run()
    # Assert
    assert calls == ["bitbucket"]


def test_python_dash_m_runs_the_cli(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    # Arrange
    monkeypatch.setattr("sys.argv", ["bitbucket", "--version"])
    # Act
    with pytest.raises(SystemExit) as caught:
        runpy.run_module("bitbucket_unofficial_cli", run_name="__main__")
    # Assert
    assert caught.value.code == 0
    assert capsys.readouterr().out == f"bitbucket {__version__}\n"

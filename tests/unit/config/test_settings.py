from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from bitbucket_unofficial_cli.config.paths import config_dir
from bitbucket_unofficial_cli.config.paths import credentials_file
from bitbucket_unofficial_cli.config.paths import settings_file
from bitbucket_unofficial_cli.config.settings import GlobalOptions
from bitbucket_unofficial_cli.config.settings import OutputFormat
from bitbucket_unofficial_cli.config.settings import Profile
from bitbucket_unofficial_cli.config.settings import Settings
from bitbucket_unofficial_cli.config.settings import resolve_options
from bitbucket_unofficial_cli.config.store import SettingsStore
from bitbucket_unofficial_cli.config.store import read_toml
from bitbucket_unofficial_cli.runtime.errors import CliError
from bitbucket_unofficial_cli.runtime.exit_codes import ExitCode

if TYPE_CHECKING:
    from pathlib import Path


def test_paths_follow_the_override_or_the_platform_directory(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    # Arrange
    monkeypatch.delenv("BITBUCKET_CLI_CONFIG_DIR", raising=False)
    default = config_dir()
    monkeypatch.setenv("BITBUCKET_CLI_CONFIG_DIR", str(tmp_path))
    # Act
    overridden = config_dir()
    # Assert
    assert default.name == "bitbucket-cli"
    assert overridden == tmp_path
    assert settings_file() == tmp_path / "config.toml"
    assert credentials_file() == tmp_path / "credentials.toml"


def test_output_defaults_to_a_table_on_a_terminal_and_json_otherwise() -> None:
    # Arrange
    settings = Settings()
    # Act
    tty = resolve_options(GlobalOptions(), settings, is_tty=True)
    pipe = resolve_options(GlobalOptions(), settings, is_tty=False)
    # Assert
    assert tty.output is OutputFormat.TABLE
    assert pipe.output is OutputFormat.JSON


def test_flags_beat_the_settings_file_which_beats_the_fallback() -> None:
    # Arrange
    settings = Settings(output=OutputFormat.CSV, profiles={"work": Profile(workspace="acme")}, default_profile="work")
    # Act
    from_settings = resolve_options(GlobalOptions(), settings, is_tty=True)
    from_flag = resolve_options(GlobalOptions(output=OutputFormat.ID, workspace="other"), settings, is_tty=True)
    # Assert
    assert (from_settings.output, from_settings.workspace) == (OutputFormat.CSV, "acme")
    assert (from_flag.output, from_flag.workspace) == (OutputFormat.ID, "other")


def test_an_unknown_profile_resolves_to_an_empty_one() -> None:
    # Arrange
    # Act
    resolved = resolve_options(GlobalOptions(profile="ghost"), Settings(), is_tty=False)
    # Assert
    assert resolved.profile_name == "ghost"
    assert resolved.profile == Profile()


def test_with_and_without_profile_do_not_mutate() -> None:
    # Arrange
    base = Settings()
    # Act
    added = base.with_profile("a", Profile())
    removed = added.without_profile("a")
    # Assert
    assert base.profiles == {}
    assert "a" in added.profiles
    assert removed.profiles == {}


def test_the_settings_store_round_trips_and_keeps_the_file_owner_only(tmp_path: Path) -> None:
    # Arrange
    store = SettingsStore(tmp_path / "nested" / "config.toml")
    settings = Settings(output=OutputFormat.JSON).with_profile("work", Profile(workspace="acme"))
    # Act
    store.save(settings)
    loaded = store.load()
    # Assert
    assert loaded == settings
    assert (tmp_path / "nested" / "config.toml").stat().st_mode & 0o777 == 0o600


def test_a_missing_file_loads_the_defaults(tmp_path: Path) -> None:
    # Arrange
    store = SettingsStore(tmp_path / "config.toml")
    # Act
    loaded = store.load()
    # Assert
    assert loaded == Settings()


@pytest.mark.parametrize("content", ["not = [valid", 'unknown_key = "x"'])
def test_a_broken_settings_file_is_a_configuration_error(tmp_path: Path, content: str) -> None:
    # Arrange
    path = tmp_path / "config.toml"
    path.write_text(content)
    # Act
    with pytest.raises(CliError) as caught:
        SettingsStore(path).load()
    # Assert
    assert caught.value.exit_code is ExitCode.CONFIGURATION


def test_read_toml_reports_a_parse_error(tmp_path: Path) -> None:
    # Arrange
    path = tmp_path / "bad.toml"
    path.write_text("= nope")
    # Act
    with pytest.raises(CliError) as caught:
        read_toml(path)
    # Assert
    assert str(path) in caught.value.message

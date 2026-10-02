from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Final

from bitbucket_unofficial_cli.config.settings import Profile
from bitbucket_unofficial_cli.config.settings import Settings
from bitbucket_unofficial_cli.runtime.exit_codes import ExitCode

if TYPE_CHECKING:
    from typer import Typer
    from typer.testing import CliRunner

# What 1.0.0 freezes. Changing any of these is a breaking change and needs a major version.
EXIT_CODES: Final = {
    "OK": 0,
    "FAILURE": 1,
    "USAGE": 2,
    "CONFIGURATION": 3,
    "AUTHENTICATION": 4,
    "FORBIDDEN": 5,
    "NOT_FOUND": 6,
    "VALIDATION": 7,
    "RATE_LIMITED": 8,
    "UNAVAILABLE": 9,
}
COMMAND_GROUPS: Final = frozenset({
    "annotation",
    "auth",
    "branch",
    "branch-restriction",
    "branching-model",
    "commit",
    "config",
    "default-reviewer",
    "deploy-key",
    "deployment",
    "download",
    "environment",
    "hook-event",
    "member",
    "permission",
    "permission-config",
    "pipeline",
    "pr",
    "project",
    "ref",
    "repo",
    "report",
    "search",
    "snippet",
    "source",
    "tag",
    "team",
    "user",
    "webhook",
    "workspace",
})
SETTINGS_KEYS: Final = frozenset({"default_profile", "output", "profiles"})
PROFILE_KEYS: Final = frozenset({"workspace", "account_id", "display_name"})
GLOBAL_OPTIONS: Final = frozenset({"--profile", "--workspace", "--output", "--verbose", "--version"})


def test_exit_codes_keep_their_values() -> None:
    # Arrange
    expected = EXIT_CODES
    # Act
    actual = {code.name: code.value for code in ExitCode}
    # Assert
    assert actual == expected


def test_the_command_groups_are_the_documented_ones(cli: Typer, runner: CliRunner) -> None:
    # Arrange
    names = frozenset(group.name for group in cli.registered_groups)
    # Act
    result = runner.invoke(cli, ["--help"])
    # Assert
    assert names == COMMAND_GROUPS
    assert result.exit_code == ExitCode.OK


def test_the_global_options_keep_their_names(cli: Typer, runner: CliRunner) -> None:
    # Arrange
    # Act
    result = runner.invoke(cli, ["--help"])
    # Assert
    assert all(option in result.stdout for option in GLOBAL_OPTIONS)


def test_the_settings_file_keeps_its_keys() -> None:
    # Arrange
    # Act
    settings = frozenset(Settings.model_fields)
    profile = frozenset(Profile.model_fields)
    # Assert
    assert settings == SETTINGS_KEYS
    assert profile == PROFILE_KEYS

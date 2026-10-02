from __future__ import annotations

import json
import os
from typing import TYPE_CHECKING
from typing import Final

import pytest
from typer.testing import CliRunner

from bitbucket_unofficial_cli.main import create_app
from bitbucket_unofficial_cli.main import default_services
from bitbucket_unofficial_cli.runtime.exit_codes import ExitCode

if TYPE_CHECKING:
    from pathlib import Path

REQUIRED: Final = ("ATLASSIAN_USER_EMAIL", "ATLASSIAN_API_TOKEN", "BITBUCKET_WORKSPACE")


def missing_variables() -> list[str]:
    return [variable for variable in REQUIRED if not os.environ.get(variable)]


@pytest.mark.live
@pytest.mark.skipif(bool(missing_variables()), reason=f"needs {', '.join(REQUIRED)}")
def test_user_me_and_repo_list_against_the_real_api(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    # Arrange
    monkeypatch.setenv("BITBUCKET_CLI_CONFIG_DIR", str(tmp_path))
    cli = create_app(default_services)
    runner = CliRunner()
    # Act
    me = runner.invoke(cli, ["-o", "json", "user", "me"])
    repositories = runner.invoke(cli, ["-o", "json", "repo", "list", "--limit", "3"])
    # Assert
    assert me.exit_code == ExitCode.OK
    assert json.loads(me.stdout)["account_id"]
    assert repositories.exit_code == ExitCode.OK
    assert isinstance(json.loads(repositories.stdout), list)

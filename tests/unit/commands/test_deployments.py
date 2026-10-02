from __future__ import annotations

import json
from typing import TYPE_CHECKING
from typing import Final

import httpx
import respx

from bitbucket_unofficial_cli.runtime.exit_codes import ExitCode
from tests.unit.commands.support import REPOS
from tests.unit.commands.support import body_of
from tests.unit.commands.support import page
from tests.unit.commands.support import run

if TYPE_CHECKING:
    from typer import Typer
    from typer.testing import CliRunner

BASE: Final = f"{REPOS}/widgets"
REPO: Final = ["--repo", "widgets"]
ENVIRONMENT: Final[dict[str, object]] = {"uuid": "{e}", "name": "Production"}
VARIABLE: Final[dict[str, object]] = {"uuid": "{v}", "key": "TOKEN", "value": "hunter2", "secured": True}
DEPLOYMENT: Final[dict[str, object]] = {
    "uuid": "{d}",
    "environment": ENVIRONMENT,
    "state": {"name": "COMPLETED", "status": {"name": "SUCCESSFUL"}},
    "release": {"name": "r1", "commit": {"hash": "abc"}},
}


@respx.mock
def test_environment_commands(cli: Typer, runner: CliRunner, environ: dict[str, str]) -> None:
    # Arrange
    url = f"{BASE}/environments"
    respx.get(url).mock(return_value=page([ENVIRONMENT]))
    respx.get(f"{url}/{{e}}").mock(return_value=httpx.Response(200, json=ENVIRONMENT))
    created = respx.post(url).mock(return_value=httpx.Response(201, json=ENVIRONMENT))
    updated = respx.post(f"{url}/{{e}}/changes").mock(return_value=httpx.Response(202))
    deleted = respx.delete(f"{url}/{{e}}").mock(return_value=httpx.Response(204))
    # Act
    listed = run(cli, runner, environ, "environment", "list", *REPO)
    got = run(cli, runner, environ, "environment", "get", "{e}", *REPO)
    create = run(cli, runner, environ, "environment", "create", *REPO, "--name", "Production")
    update = run(cli, runner, environ, "environment", "update", "{e}", *REPO, "--name", "Prod")
    delete = run(cli, runner, environ, "environment", "delete", "{e}", *REPO, "--yes")
    # Assert
    assert json.loads(listed.stdout)[0]["name"] == "Production"
    assert json.loads(got.stdout)["uuid"] == "{e}"
    assert body_of(created.calls.last.request) == {"type": "deployment_environment", "name": "Production"}
    assert body_of(updated.calls.last.request) == {"name": "Prod"}
    assert json.loads(update.stdout)["uuid"] == "{e}"
    assert create.exit_code == delete.exit_code == ExitCode.OK
    assert deleted.called


@respx.mock
def test_environment_variable_commands_never_print_values(
    cli: Typer, runner: CliRunner, environ: dict[str, str]
) -> None:
    # Arrange
    url = f"{BASE}/deployments_config/environments/{{e}}/variables"
    respx.get(url).mock(return_value=page([VARIABLE]))
    created = respx.post(url).mock(return_value=httpx.Response(201, json=VARIABLE))
    updated = respx.put(f"{url}/{{v}}").mock(return_value=httpx.Response(200, json=VARIABLE))
    deleted = respx.delete(f"{url}/{{v}}").mock(return_value=httpx.Response(204))
    # Act
    listed = run(cli, runner, environ, "environment", "variable", "list", "{e}", *REPO)
    create = run(
        cli, runner, environ, "environment", "variable", "create", "{e}", "TOKEN", *REPO, "--stdin", stdin="v1\n"
    )
    update = run(cli, runner, environ, "environment", "variable", "update", "{e}", "{v}", *REPO, "--stdin", stdin="v2")
    rename = run(cli, runner, environ, "environment", "variable", "update", "{e}", "{v}", *REPO, "--key", "NEW")
    delete = run(cli, runner, environ, "environment", "variable", "delete", "{e}", "{v}", *REPO, "--yes")
    # Assert
    assert "hunter2" not in listed.stdout + create.stdout + update.stdout
    assert json.loads(listed.stdout)[0]["key"] == "TOKEN"
    assert body_of(created.calls.last.request) == {"key": "TOKEN", "value": "v1"}
    assert body_of(updated.calls[0].request) == {"value": "v2"}
    assert body_of(updated.calls[1].request) == {"key": "NEW"}
    assert create.exit_code == update.exit_code == rename.exit_code == delete.exit_code == ExitCode.OK
    assert deleted.called


@respx.mock
def test_deployment_commands(cli: Typer, runner: CliRunner, environ: dict[str, str]) -> None:
    # Arrange
    respx.get(f"{BASE}/deployments").mock(return_value=page([DEPLOYMENT]))
    respx.get(f"{BASE}/deployments/{{d}}").mock(return_value=httpx.Response(200, json=DEPLOYMENT))
    # Act
    listed = run(cli, runner, environ, "deployment", "list", *REPO)
    got = run(cli, runner, environ, "deployment", "get", "{d}", *REPO)
    # Assert
    assert json.loads(listed.stdout)[0]["state"]["status"]["name"] == "SUCCESSFUL"
    assert json.loads(got.stdout)["release"]["commit"]["hash"] == "abc"

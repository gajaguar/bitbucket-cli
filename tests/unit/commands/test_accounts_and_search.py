from __future__ import annotations

import json
from typing import TYPE_CHECKING
from typing import Final

import httpx
import respx

from bitbucket_unofficial_cli.runtime.exit_codes import ExitCode
from tests.conftest import BASE_URL
from tests.conftest import USER_PAYLOAD
from tests.unit.commands.support import WORKSPACE
from tests.unit.commands.support import body_of
from tests.unit.commands.support import page
from tests.unit.commands.support import run

if TYPE_CHECKING:
    from pathlib import Path

    from typer import Typer
    from typer.testing import CliRunner

ME: Final = f"{BASE_URL}/users/557058:abc"
OTHER: Final = f"{BASE_URL}/users/other"
EMAIL: Final[dict[str, object]] = {"email": "me@example.com", "is_primary": True, "is_confirmed": True}
SSH: Final[dict[str, object]] = {"uuid": "{k}", "label": "laptop", "fingerprint": "SHA256:x"}
GPG: Final[dict[str, object]] = {"fingerprint": "ABCD", "name": "work", "key_id": "1234"}
VARIABLE: Final[dict[str, object]] = {"uuid": "{v}", "key": "TOKEN", "value": "hunter2", "secured": True}
HIT: Final[dict[str, object]] = {"file": {"path": "a.py", "commit": {"hash": "abc"}}, "content_match_count": 2}


@respx.mock
def test_user_get_shows_another_user(cli: Typer, runner: CliRunner, environ: dict[str, str]) -> None:
    # Arrange
    respx.get(OTHER).mock(return_value=httpx.Response(200, json=USER_PAYLOAD))
    # Act
    result = run(cli, runner, environ, "user", "get", "other")
    # Assert
    assert json.loads(result.stdout)["account_id"] == "557058:abc"


@respx.mock
def test_user_email_commands(cli: Typer, runner: CliRunner, environ: dict[str, str]) -> None:
    # Arrange
    respx.get(f"{BASE_URL}/user/emails").mock(return_value=page([EMAIL]))
    respx.get(f"{BASE_URL}/user/emails/me@example.com").mock(return_value=httpx.Response(200, json=EMAIL))
    # Act
    listed = run(cli, runner, environ, "user", "email", "list")
    got = run(cli, runner, environ, "user", "email", "get", "me@example.com")
    # Assert
    assert json.loads(listed.stdout)[0]["is_primary"] is True
    assert json.loads(got.stdout)["email"] == "me@example.com"


@respx.mock
def test_user_ssh_key_commands_default_to_the_current_user(
    cli: Typer, runner: CliRunner, environ: dict[str, str], tmp_path: Path
) -> None:
    # Arrange
    respx.get(f"{BASE_URL}/user").mock(return_value=httpx.Response(200, json=USER_PAYLOAD))
    respx.get(f"{ME}/ssh-keys").mock(return_value=page([SSH]))
    respx.get(f"{ME}/ssh-keys/{{k}}").mock(return_value=httpx.Response(200, json=SSH))
    created = respx.post(f"{ME}/ssh-keys").mock(return_value=httpx.Response(201, json=SSH))
    updated = respx.put(f"{ME}/ssh-keys/{{k}}").mock(return_value=httpx.Response(200, json=SSH))
    deleted = respx.delete(f"{ME}/ssh-keys/{{k}}").mock(return_value=httpx.Response(204))
    key_file = tmp_path / "id.pub"
    key_file.write_text("ssh-ed25519 FROMFILE\n")
    # Act
    listed = run(cli, runner, environ, "user", "ssh-key", "list")
    got = run(cli, runner, environ, "user", "ssh-key", "get", "{k}")
    inline = run(
        cli, runner, environ, "user", "ssh-key", "create", "--key", "ssh-ed25519 AAA", "--label", "laptop",
        "--expires-on", "2030-01-01T00:00:00Z",
    )  # fmt: skip
    from_file = run(cli, runner, environ, "user", "ssh-key", "create", "--key-file", str(key_file))
    unreadable = run(cli, runner, environ, "user", "ssh-key", "create", "--key-file", str(tmp_path / "nope"))
    update = run(cli, runner, environ, "user", "ssh-key", "update", "{k}", "--label", "desk")
    delete = run(cli, runner, environ, "user", "ssh-key", "delete", "{k}", "--yes")
    # Assert
    assert json.loads(listed.stdout)[0]["label"] == "laptop"
    assert json.loads(got.stdout)["uuid"] == "{k}"
    assert body_of(created.calls[0].request) == {"key": "ssh-ed25519 AAA", "label": "laptop"}
    assert created.calls[0].request.url.params["expires_on"] == "2030-01-01T00:00:00Z"
    assert body_of(created.calls[1].request) == {"key": "ssh-ed25519 FROMFILE"}
    assert inline.exit_code == from_file.exit_code == ExitCode.OK
    assert unreadable.exit_code == ExitCode.USAGE
    assert body_of(updated.calls.last.request) == {"label": "desk"}
    assert update.exit_code == delete.exit_code == ExitCode.OK
    assert deleted.called


@respx.mock
def test_user_gpg_key_commands_for_an_explicit_user(cli: Typer, runner: CliRunner, environ: dict[str, str]) -> None:
    # Arrange
    respx.get(f"{OTHER}/gpg-keys").mock(return_value=page([GPG]))
    respx.get(f"{OTHER}/gpg-keys/ABCD").mock(return_value=httpx.Response(200, json=GPG))
    created = respx.post(f"{OTHER}/gpg-keys").mock(return_value=httpx.Response(201, json=GPG))
    deleted = respx.delete(f"{OTHER}/gpg-keys/ABCD").mock(return_value=httpx.Response(204))
    # Act
    listed = run(cli, runner, environ, "user", "gpg-key", "list", "--user", "other")
    got = run(cli, runner, environ, "user", "gpg-key", "get", "ABCD", "--user", "other")
    create = run(
        cli, runner, environ, "user", "gpg-key", "create", "--user", "other", "--key", "KEY", "--name", "work"
    )
    delete = run(cli, runner, environ, "user", "gpg-key", "delete", "ABCD", "--user", "other", "--yes")
    # Assert
    assert json.loads(listed.stdout)[0]["fingerprint"] == "ABCD"
    assert json.loads(got.stdout)["name"] == "work"
    assert body_of(created.calls.last.request) == {"key": "KEY", "name": "work"}
    assert create.exit_code == delete.exit_code == ExitCode.OK
    assert deleted.called


@respx.mock
def test_user_variable_commands_never_print_values(cli: Typer, runner: CliRunner, environ: dict[str, str]) -> None:
    # Arrange
    url = f"{OTHER}/pipelines_config/variables"
    respx.get(url).mock(return_value=page([VARIABLE]))
    respx.get(f"{url}/{{v}}").mock(return_value=httpx.Response(200, json=VARIABLE))
    created = respx.post(url).mock(return_value=httpx.Response(201, json=VARIABLE))
    updated = respx.put(f"{url}/{{v}}").mock(return_value=httpx.Response(200, json=VARIABLE))
    deleted = respx.delete(f"{url}/{{v}}").mock(return_value=httpx.Response(204))
    scope = ["--user", "other"]
    # Act
    listed = run(cli, runner, environ, "user", "variable", "list", *scope)
    got = run(cli, runner, environ, "user", "variable", "get", "{v}", *scope)
    create = run(cli, runner, environ, "user", "variable", "create", "TOKEN", *scope, "--stdin", stdin="v1\n")
    update = run(cli, runner, environ, "user", "variable", "update", "{v}", *scope, "--stdin", "--secured", stdin="v2")
    delete = run(cli, runner, environ, "user", "variable", "delete", "{v}", *scope, "--yes")
    # Assert
    assert "hunter2" not in listed.stdout + got.stdout + create.stdout + update.stdout
    assert body_of(created.calls.last.request) == {"key": "TOKEN", "value": "v1"}
    assert body_of(updated.calls.last.request) == {"value": "v2", "secured": True}
    assert create.exit_code == update.exit_code == delete.exit_code == ExitCode.OK
    assert deleted.called


@respx.mock
def test_team_variable_commands(cli: Typer, runner: CliRunner, environ: dict[str, str]) -> None:
    # Arrange
    url = f"{BASE_URL}/teams/devs/pipelines_config/variables"
    respx.get(url).mock(return_value=page([VARIABLE]))
    respx.get(f"{url}/{{v}}").mock(return_value=httpx.Response(200, json=VARIABLE))
    created = respx.post(url).mock(return_value=httpx.Response(201, json=VARIABLE))
    deleted = respx.delete(f"{url}/{{v}}").mock(return_value=httpx.Response(204))
    # Act
    listed = run(cli, runner, environ, "team", "variable", "list", "--team", "devs")
    got = run(cli, runner, environ, "team", "variable", "get", "{v}", "--team", "devs")
    create = run(cli, runner, environ, "team", "variable", "create", "TOKEN", "--team", "devs", "--stdin", stdin="v")
    delete = run(cli, runner, environ, "team", "variable", "delete", "{v}", "--team", "devs", "--yes")
    # Assert
    assert json.loads(listed.stdout)[0]["key"] == "TOKEN"
    assert json.loads(got.stdout)["uuid"] == "{v}"
    assert body_of(created.calls.last.request) == {"key": "TOKEN", "value": "v"}
    assert create.exit_code == delete.exit_code == ExitCode.OK
    assert deleted.called


@respx.mock
def test_search_code_in_the_workspace_a_user_and_a_team(
    cli: Typer, runner: CliRunner, environ: dict[str, str]
) -> None:
    # Arrange
    workspace = respx.get(f"{WORKSPACE}/search/code").mock(return_value=page([HIT]))
    respx.get(f"{OTHER}/search/code").mock(return_value=page([HIT]))
    respx.get(f"{BASE_URL}/teams/devs/search/code").mock(return_value=page([HIT]))
    # Act
    in_workspace = run(cli, runner, environ, "search", "code", "def main", "--fields", "values.file.path")
    in_user = run(cli, runner, environ, "search", "code", "def main", "--user", "other")
    in_team = run(cli, runner, environ, "search", "code", "def main", "--team", "devs")
    both = run(cli, runner, environ, "search", "code", "x", "--user", "other", "--team", "devs")
    # Assert
    assert json.loads(in_workspace.stdout)[0]["file"]["path"] == "a.py"
    assert dict(workspace.calls.last.request.url.params) == {
        "search_query": "def main",
        "fields": "values.file.path",
    }
    assert json.loads(in_user.stdout)[0]["content_match_count"] == 2
    assert json.loads(in_team.stdout)[0]["content_match_count"] == 2
    assert both.exit_code == ExitCode.USAGE


@respx.mock
def test_team_variable_update_changes_the_value_and_the_name(
    cli: Typer, runner: CliRunner, environ: dict[str, str]
) -> None:
    # Arrange
    route = respx.put(f"{BASE_URL}/teams/devs/pipelines_config/variables/{{v}}").mock(
        return_value=httpx.Response(200, json=VARIABLE)
    )
    # Act
    result = run(
        cli, runner, environ, "team", "variable", "update", "{v}", "--team", "devs", "--key", "NEW", "--stdin",
        stdin="fresh\n",
    )  # fmt: skip
    # Assert
    assert result.exit_code == ExitCode.OK
    assert body_of(route.calls.last.request) == {"key": "NEW", "value": "fresh"}


@respx.mock
def test_a_user_command_without_user_fails_when_bitbucket_omits_the_account_id(
    cli: Typer, runner: CliRunner, environ: dict[str, str]
) -> None:
    # Arrange
    respx.get(f"{BASE_URL}/user").mock(return_value=httpx.Response(200, json={"display_name": "Nameless"}))
    # Act
    result = run(cli, runner, environ, "user", "ssh-key", "list")
    # Assert
    assert result.exit_code == ExitCode.FAILURE
    assert "--user" in result.stderr

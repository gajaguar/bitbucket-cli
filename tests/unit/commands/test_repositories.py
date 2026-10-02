from __future__ import annotations

import json
from typing import TYPE_CHECKING
from typing import Final

import httpx
import respx

from bitbucket_unofficial_cli.runtime.exit_codes import ExitCode
from tests.conftest import BASE_URL
from tests.conftest import REPOSITORY_PAYLOAD
from tests.unit.commands.support import REPOS
from tests.unit.commands.support import WORKSPACE
from tests.unit.commands.support import body_of
from tests.unit.commands.support import page
from tests.unit.commands.support import run

if TYPE_CHECKING:
    from typer import Typer
    from typer.testing import CliRunner

PROJECT: Final[dict[str, object]] = {"type": "project", "key": "WID", "name": "Widgets", "is_private": True}
MEMBER: Final[dict[str, object]] = {
    "type": "workspace_membership",
    "permission": "owner",
    "user": {"type": "user", "display_name": "Some One", "account_id": "557058:abc"},
}


@respx.mock
def test_repo_create_sends_the_flags_in_the_body(cli: Typer, runner: CliRunner, environ: dict[str, str]) -> None:
    # Arrange
    route = respx.post(f"{REPOS}/widgets").mock(return_value=httpx.Response(200, json=REPOSITORY_PAYLOAD))
    # Act
    result = run(
        cli,
        runner,
        environ,
        *["repo", "create", "widgets", "--private", "--project", "WID", "--fork-policy", "no_forks", "--no-wiki"],
    )
    # Assert
    assert result.exit_code == ExitCode.OK
    assert body_of(route.calls.last.request) == {
        "is_private": True,
        "project": {"key": "WID"},
        "fork_policy": "no_forks",
        "has_wiki": False,
    }


@respx.mock
def test_repo_create_merges_a_json_file_with_the_flags(cli: Typer, runner: CliRunner, environ: dict[str, str]) -> None:
    # Arrange
    route = respx.post(f"{REPOS}/widgets").mock(return_value=httpx.Response(200, json=REPOSITORY_PAYLOAD))
    body = json.dumps({"description": "from file", "language": "go"})
    # Act
    result = run(
        cli, runner, environ, *["repo", "create", "widgets", "--from-file", "-", "--language", "python"], stdin=body
    )
    # Assert
    assert result.exit_code == ExitCode.OK
    assert body_of(route.calls.last.request) == {"description": "from file", "language": "python"}


def test_repo_create_rejects_a_body_that_is_not_an_object(
    cli: Typer, runner: CliRunner, environ: dict[str, str]
) -> None:
    # Arrange
    environ["BITBUCKET_PROFILE"] = "default"
    # Act
    result = run(cli, runner, environ, *["repo", "create", "widgets", "--from-file", "-"], stdin="[1]")
    # Assert
    assert result.exit_code == ExitCode.USAGE


def test_repo_create_rejects_unreadable_json(cli: Typer, runner: CliRunner, environ: dict[str, str]) -> None:
    # Arrange
    environ["BITBUCKET_PROFILE"] = "default"
    # Act
    result = run(cli, runner, environ, *["repo", "create", "widgets", "--from-file", "-"], stdin="{")
    # Assert
    assert result.exit_code == ExitCode.USAGE


def test_repo_create_rejects_a_missing_file(cli: Typer, runner: CliRunner, environ: dict[str, str]) -> None:
    # Arrange
    environ["BITBUCKET_PROFILE"] = "default"
    # Act
    result = run(cli, runner, environ, *["repo", "create", "widgets", "--from-file", "/nonexistent.json"])
    # Assert
    assert result.exit_code == ExitCode.USAGE


def test_repo_create_rejects_a_body_the_model_refuses(cli: Typer, runner: CliRunner, environ: dict[str, str]) -> None:
    # Arrange
    environ["BITBUCKET_PROFILE"] = "default"
    # Act
    result = run(cli, runner, environ, *["repo", "create", "widgets", "--from-file", "-"], stdin='{"is_private": []}')
    # Assert
    assert result.exit_code == ExitCode.USAGE


@respx.mock
def test_repo_update_puts_the_changed_fields(cli: Typer, runner: CliRunner, environ: dict[str, str]) -> None:
    # Arrange
    route = respx.put(f"{REPOS}/widgets").mock(return_value=httpx.Response(200, json=REPOSITORY_PAYLOAD))
    # Act
    result = run(cli, runner, environ, *["repo", "update", "widgets", "--description", "new", "--public"])
    # Assert
    assert result.exit_code == ExitCode.OK
    assert body_of(route.calls.last.request) == {"description": "new", "is_private": False}


@respx.mock
def test_repo_delete_with_yes_deletes(cli: Typer, runner: CliRunner, environ: dict[str, str]) -> None:
    # Arrange
    route = respx.delete(f"{REPOS}/widgets").mock(return_value=httpx.Response(204))
    # Act
    result = run(cli, runner, environ, *["repo", "delete", "widgets", "--yes"])
    # Assert
    assert result.exit_code == ExitCode.OK
    assert route.called


@respx.mock
def test_repo_delete_without_yes_refuses_on_a_pipe(cli: Typer, runner: CliRunner, environ: dict[str, str]) -> None:
    # Arrange
    route = respx.delete(f"{REPOS}/widgets").mock(return_value=httpx.Response(204))
    # Act
    result = run(cli, runner, environ, *["repo", "delete", "widgets"])
    # Assert
    assert result.exit_code == ExitCode.USAGE
    assert not route.called


@respx.mock
def test_repo_delete_asks_on_a_terminal_and_aborts_on_no(
    cli: Typer, runner: CliRunner, environ: dict[str, str], monkeypatch: object
) -> None:
    # Arrange
    route = respx.delete(f"{REPOS}/widgets").mock(return_value=httpx.Response(204))
    monkeypatch.setattr("bitbucket_unofficial_cli.runtime.context._interactive", lambda: True)  # type: ignore[attr-defined]
    # Act
    result = run(cli, runner, environ, *["repo", "delete", "widgets"], stdin="n\n")
    # Assert
    assert result.exit_code == ExitCode.FAILURE
    assert not route.called


@respx.mock
def test_repo_delete_asks_on_a_terminal_and_deletes_on_yes(
    cli: Typer, runner: CliRunner, environ: dict[str, str], monkeypatch: object
) -> None:
    # Arrange
    route = respx.delete(f"{REPOS}/widgets").mock(return_value=httpx.Response(204))
    monkeypatch.setattr("bitbucket_unofficial_cli.runtime.context._interactive", lambda: True)  # type: ignore[attr-defined]
    # Act
    result = run(cli, runner, environ, *["repo", "delete", "widgets"], stdin="y\n")
    # Assert
    assert result.exit_code == ExitCode.OK
    assert route.called


@respx.mock
def test_repo_fork_posts_the_target(cli: Typer, runner: CliRunner, environ: dict[str, str]) -> None:
    # Arrange
    route = respx.post(f"{REPOS}/widgets/forks").mock(return_value=httpx.Response(200, json=REPOSITORY_PAYLOAD))
    # Act
    result = run(cli, runner, environ, *["repo", "fork", "widgets", "--name", "mine", "--to-workspace", "me"])
    # Assert
    assert result.exit_code == ExitCode.OK
    assert body_of(route.calls.last.request) == {"name": "mine", "workspace": {"slug": "me"}}


@respx.mock
def test_repo_forks_and_watchers_list(cli: Typer, runner: CliRunner, environ: dict[str, str]) -> None:
    # Arrange
    respx.get(f"{REPOS}/widgets/forks").mock(return_value=page([REPOSITORY_PAYLOAD]))
    respx.get(f"{REPOS}/widgets/watchers").mock(return_value=page([{"display_name": "Some One", "account_id": "a"}]))
    # Act
    forks = run(cli, runner, environ, "repo", "forks", "widgets")
    watchers = run(cli, runner, environ, "-o", "id", "repo", "watchers", "widgets", output="id")
    # Assert
    assert json.loads(forks.stdout)[0]["slug"] == "widgets"
    assert watchers.stdout == "a\n"


@respx.mock
def test_project_crud(cli: Typer, runner: CliRunner, environ: dict[str, str]) -> None:
    # Arrange
    respx.get(f"{WORKSPACE}/projects").mock(return_value=page([PROJECT]))
    respx.get(f"{WORKSPACE}/projects/WID").mock(return_value=httpx.Response(200, json=PROJECT))
    created = respx.post(f"{WORKSPACE}/projects").mock(return_value=httpx.Response(201, json=PROJECT))
    updated = respx.put(f"{WORKSPACE}/projects/WID").mock(return_value=httpx.Response(200, json=PROJECT))
    deleted = respx.delete(f"{WORKSPACE}/projects/WID").mock(return_value=httpx.Response(204))
    # Act
    listed = run(cli, runner, environ, "project", "list", "-q", 'name="Widgets"')
    got = run(cli, runner, environ, "project", "get", "WID")
    create = run(cli, runner, environ, *["project", "create", "WID", "--name", "Widgets", "--private"])
    update = run(cli, runner, environ, *["project", "update", "WID", "--new-key", "WID2", "--description", "d"])
    delete = run(cli, runner, environ, "project", "delete", "WID", "--yes")
    # Assert
    assert json.loads(listed.stdout)[0]["key"] == "WID"
    assert json.loads(got.stdout)["name"] == "Widgets"
    assert create.exit_code == update.exit_code == delete.exit_code == ExitCode.OK
    assert body_of(created.calls.last.request) == {"key": "WID", "name": "Widgets", "is_private": True}
    assert body_of(updated.calls.last.request) == {"key": "WID2", "description": "d"}
    assert deleted.called


@respx.mock
def test_member_and_permission_commands(cli: Typer, runner: CliRunner, environ: dict[str, str]) -> None:
    # Arrange
    permission = {"type": "repository_permission", "permission": "admin", "repository": REPOSITORY_PAYLOAD}
    respx.get(f"{WORKSPACE}/members").mock(return_value=page([MEMBER]))
    respx.get(f"{WORKSPACE}/members/557058:abc").mock(return_value=httpx.Response(200, json=MEMBER))
    respx.get(f"{WORKSPACE}/permissions").mock(return_value=page([MEMBER]))
    respx.get(f"{WORKSPACE}/permissions/repositories").mock(return_value=page([permission]))
    respx.get(f"{WORKSPACE}/permissions/repositories/widgets").mock(return_value=page([permission]))
    respx.get(f"{BASE_URL}/user/workspaces/acme/permission").mock(return_value=httpx.Response(200, json=MEMBER))
    respx.get(f"{BASE_URL}/user/workspaces/acme/permissions/repositories").mock(return_value=page([permission]))
    # Act
    members = run(cli, runner, environ, "member", "list")
    member = run(cli, runner, environ, "member", "get", "557058:abc")
    everyone = run(cli, runner, environ, "permission", "list")
    repositories = run(cli, runner, environ, "permission", "list", "--repositories")
    one = run(cli, runner, environ, "permission", "list", "--repository", "widgets")
    mine = run(cli, runner, environ, "permission", "mine")
    mine_repositories = run(cli, runner, environ, "permission", "mine", "--repositories")
    # Assert
    assert json.loads(members.stdout)[0]["permission"] == "owner"
    assert json.loads(member.stdout)["permission"] == "owner"
    assert json.loads(everyone.stdout)[0]["permission"] == "owner"
    assert json.loads(repositories.stdout)[0]["permission"] == "admin"
    assert json.loads(one.stdout)[0]["permission"] == "admin"
    assert json.loads(mine.stdout)["permission"] == "owner"
    assert json.loads(mine_repositories.stdout)[0]["permission"] == "admin"


def test_permission_list_rejects_both_scopes(cli: Typer, runner: CliRunner, environ: dict[str, str]) -> None:
    # Arrange
    environ["BITBUCKET_PROFILE"] = "default"
    # Act
    result = run(cli, runner, environ, "permission", "list", "--repositories", "--repository", "widgets")
    # Assert
    assert result.exit_code == ExitCode.USAGE


@respx.mock
def test_webhook_crud_on_a_repository_and_on_the_workspace(
    cli: Typer, runner: CliRunner, environ: dict[str, str]
) -> None:
    # Arrange
    hook = {"uuid": "{h}", "url": "https://x.test", "description": "d", "active": True, "events": ["repo:push"]}
    respx.get(f"{REPOS}/widgets/hooks").mock(return_value=page([hook]))
    respx.get(f"{WORKSPACE}/hooks/{{h}}").mock(return_value=httpx.Response(200, json=hook))
    created = respx.post(f"{REPOS}/widgets/hooks").mock(return_value=httpx.Response(201, json=hook))
    updated = respx.put(f"{WORKSPACE}/hooks/{{h}}").mock(return_value=httpx.Response(200, json=hook))
    deleted = respx.delete(f"{REPOS}/widgets/hooks/{{h}}").mock(return_value=httpx.Response(204))
    # Act
    listed = run(cli, runner, environ, "webhook", "list", "--repo", "widgets")
    got = run(cli, runner, environ, "webhook", "get", "{h}")
    create = run(
        cli,
        runner,
        environ,
        *["webhook", "create", "-r", "widgets", "--description", "d", "--url", "https://x.test"],
        *["--event", "repo:push", "--active"],
    )
    update = run(cli, runner, environ, "webhook", "update", "{h}", "--inactive")
    delete = run(cli, runner, environ, "webhook", "delete", "{h}", "-r", "widgets", "--yes")
    # Assert
    assert json.loads(listed.stdout)[0]["url"] == "https://x.test"
    assert json.loads(got.stdout)["uuid"] == "{h}"
    assert create.exit_code == update.exit_code == delete.exit_code == ExitCode.OK
    assert body_of(created.calls.last.request) == {
        "description": "d",
        "url": "https://x.test",
        "events": ["repo:push"],
        "active": True,
    }
    assert body_of(updated.calls.last.request) == {"active": False}
    assert deleted.called


@respx.mock
def test_hook_events(cli: Typer, runner: CliRunner, environ: dict[str, str]) -> None:
    # Arrange
    respx.get(f"{BASE_URL}/hook_events").mock(
        return_value=httpx.Response(200, json={"repository": {"links": {"events": {"href": "https://x.test"}}}})
    )
    respx.get(f"{BASE_URL}/hook_events/repository").mock(
        return_value=page([{"event": "repo:push", "category": "Repository", "label": "Push", "description": "d"}])
    )
    # Act
    types = run(cli, runner, environ, "hook-event", "types")
    events = run(cli, runner, environ, "hook-event", "list", "repository")
    # Assert
    assert json.loads(types.stdout)[0]["subject_type"] == "repository"
    assert json.loads(events.stdout)[0]["event"] == "repo:push"


@respx.mock
def test_workspace_gpg_key_prints_the_raw_key(cli: Typer, runner: CliRunner, environ: dict[str, str]) -> None:
    # Arrange
    respx.get(f"{WORKSPACE}/settings/gpg/public-key").mock(return_value=httpx.Response(200, text="-----KEY-----"))
    # Act
    result = run(cli, runner, environ, "workspace", "gpg-key")
    # Assert
    assert result.stdout == "-----KEY-----\n"

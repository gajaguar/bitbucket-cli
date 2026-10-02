from __future__ import annotations

import json
from typing import TYPE_CHECKING
from typing import Final

import httpx
import respx

from bitbucket_unofficial_cli.runtime.exit_codes import ExitCode
from tests.unit.commands.support import REPOS
from tests.unit.commands.support import WORKSPACE
from tests.unit.commands.support import body_of
from tests.unit.commands.support import page
from tests.unit.commands.support import run

if TYPE_CHECKING:
    import pytest
    from typer import Typer
    from typer.testing import CliRunner

BASE: Final = f"{REPOS}/widgets"
PROJECT: Final = f"{WORKSPACE}/projects/WID"
REPO: Final = ["--repo", "widgets"]
SCOPE: Final = ["--project", "WID"]
RESTRICTION: Final[dict[str, object]] = {"id": 5, "kind": "push", "branch_match_kind": "glob", "pattern": "main"}
MODEL: Final[dict[str, object]] = {"development": {"name": "dev"}, "production": {"name": "main"}}
SETTINGS: Final[dict[str, object]] = {"development": {"name": "dev", "enabled": True}}
REVIEWER: Final[dict[str, object]] = {"display_name": "Some One", "account_id": "a", "reviewer_type": "repository"}
PROJECT_REVIEWER: Final[dict[str, object]] = {"user": {"display_name": "Some One", "account_id": "a"}}
KEY: Final[dict[str, object]] = {"id": 9, "label": "ci", "key": "ssh-ed25519 AAA"}
GROUP: Final[dict[str, object]] = {"group": {"slug": "devs", "name": "Devs"}, "permission": "write"}
USER: Final[dict[str, object]] = {"user": {"display_name": "Some One", "account_id": "a"}, "permission": "admin"}


@respx.mock
def test_branch_restriction_commands(cli: Typer, runner: CliRunner, environ: dict[str, str]) -> None:
    # Arrange
    url = f"{BASE}/branch-restrictions"
    listing = respx.get(url).mock(return_value=page([RESTRICTION]))
    respx.get(f"{url}/5").mock(return_value=httpx.Response(200, json=RESTRICTION))
    created = respx.post(url).mock(return_value=httpx.Response(201, json=RESTRICTION))
    updated = respx.put(f"{url}/5").mock(return_value=httpx.Response(200, json=RESTRICTION))
    deleted = respx.delete(f"{url}/5").mock(return_value=httpx.Response(204))
    # Act
    listed = run(cli, runner, environ, "branch-restriction", "list", *REPO, "--kind", "push", "--pattern", "main")
    got = run(cli, runner, environ, "branch-restriction", "get", "5", *REPO)
    create = run(
        cli,
        runner,
        environ,
        *["branch-restriction", "create", *REPO, "--kind", "push", "--match", "glob", "--pattern", "main"],
        *["--branch-type", "feature", "--value", "2", "--user", "{u}", "--group", "devs"],
    )
    update = run(cli, runner, environ, "branch-restriction", "update", "5", *REPO, "--pattern", "dev")
    delete = run(cli, runner, environ, "branch-restriction", "delete", "5", *REPO, "--yes")
    # Assert
    assert json.loads(listed.stdout)[0]["id"] == 5
    assert listing.calls.last.request.url.params["kind"] == "push"
    assert json.loads(got.stdout)["kind"] == "push"
    assert body_of(created.calls.last.request) == {
        "kind": "push",
        "branch_match_kind": "glob",
        "branch_type": "feature",
        "pattern": "main",
        "value": 2,
        "users": [{"uuid": "{u}"}],
        "groups": [{"slug": "devs"}],
    }
    assert body_of(updated.calls.last.request) == {"pattern": "dev"}
    assert create.exit_code == update.exit_code == delete.exit_code == ExitCode.OK
    assert deleted.called


def test_branch_restriction_rejects_an_unknown_kind(cli: Typer, runner: CliRunner, environ: dict[str, str]) -> None:
    # Arrange
    arguments = ["branch-restriction", "create", *REPO, "--kind", "bogus"]
    # Act
    result = run(cli, runner, environ, *arguments)
    # Assert
    assert result.exit_code == ExitCode.USAGE
    assert "bogus" in result.stderr


@respx.mock
def test_branching_model_on_a_repository(cli: Typer, runner: CliRunner, environ: dict[str, str]) -> None:
    # Arrange
    respx.get(f"{BASE}/branching-model").mock(return_value=httpx.Response(200, json=MODEL))
    respx.get(f"{BASE}/effective-branching-model").mock(return_value=httpx.Response(200, json=MODEL))
    respx.get(f"{BASE}/branching-model/settings").mock(return_value=httpx.Response(200, json=SETTINGS))
    updated = respx.put(f"{BASE}/branching-model/settings").mock(return_value=httpx.Response(200, json=SETTINGS))
    # Act
    model = run(cli, runner, environ, "branching-model", "get", *REPO)
    effective = run(cli, runner, environ, "branching-model", "effective", *REPO)
    settings = run(cli, runner, environ, "branching-model", "settings", *REPO)
    update = run(
        cli,
        runner,
        environ,
        *["branching-model", "update", *REPO, "--development-name", "dev", "--no-development-main"],
        *["--production-name", "main", "--production-main", "--production"],
    )
    # Assert
    assert json.loads(model.stdout)["development"]["name"] == "dev"
    assert json.loads(effective.stdout)["production"]["name"] == "main"
    assert json.loads(settings.stdout)["development"]["enabled"] is True
    assert update.exit_code == ExitCode.OK
    assert body_of(updated.calls.last.request) == {
        "development": {"name": "dev", "use_mainbranch": False},
        "production": {"name": "main", "use_mainbranch": True, "enabled": True},
    }


@respx.mock
def test_branching_model_on_a_project(cli: Typer, runner: CliRunner, environ: dict[str, str]) -> None:
    # Arrange
    respx.get(f"{PROJECT}/branching-model").mock(return_value=httpx.Response(200, json=MODEL))
    # Act
    model = run(cli, runner, environ, "branching-model", "get", *SCOPE)
    effective = run(cli, runner, environ, "branching-model", "effective", *SCOPE)
    # Assert
    assert json.loads(model.stdout)["production"]["name"] == "main"
    assert effective.exit_code == ExitCode.USAGE


def test_a_scope_is_required_and_cannot_be_both(cli: Typer, runner: CliRunner, environ: dict[str, str]) -> None:
    # Arrange
    both = ["branching-model", "get", "--repo", "widgets", "--project", "WID"]
    # Act
    neither = run(cli, runner, environ, "branching-model", "get")
    conflicting = run(cli, runner, environ, *both)
    # Assert
    assert neither.exit_code == ExitCode.USAGE
    assert conflicting.exit_code == ExitCode.USAGE


@respx.mock
def test_project_wins_over_a_repository_from_the_environment(
    cli: Typer, runner: CliRunner, environ: dict[str, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    # Arrange
    monkeypatch.setenv("BITBUCKET_REPOSITORY", "widgets")
    route = respx.get(f"{PROJECT}/branching-model").mock(return_value=httpx.Response(200, json=MODEL))
    # Act
    result = run(cli, runner, environ, "branching-model", "get", *SCOPE)
    # Assert
    assert result.exit_code == ExitCode.OK
    assert route.called


@respx.mock
def test_default_reviewers_on_a_repository(cli: Typer, runner: CliRunner, environ: dict[str, str]) -> None:
    # Arrange
    url = f"{BASE}/default-reviewers"
    respx.get(url).mock(return_value=page([REVIEWER]))
    respx.get(f"{url}/a").mock(return_value=httpx.Response(200, json=REVIEWER))
    respx.put(f"{url}/a").mock(return_value=httpx.Response(200, json=REVIEWER))
    removed = respx.delete(f"{url}/a").mock(return_value=httpx.Response(204))
    respx.get(f"{BASE}/effective-default-reviewers").mock(return_value=page([REVIEWER]))
    # Act
    listed = run(cli, runner, environ, "default-reviewer", "list", *REPO)
    got = run(cli, runner, environ, "default-reviewer", "get", "a", *REPO)
    add = run(cli, runner, environ, "default-reviewer", "add", "a", *REPO)
    remove = run(cli, runner, environ, "default-reviewer", "remove", "a", *REPO)
    effective = run(cli, runner, environ, "default-reviewer", "effective", *REPO)
    # Assert
    assert json.loads(listed.stdout)[0]["account_id"] == "a"
    assert json.loads(got.stdout)["account_id"] == "a"
    assert add.exit_code == remove.exit_code == ExitCode.OK
    assert json.loads(effective.stdout)[0]["account_id"] == "a"
    assert removed.called


@respx.mock
def test_default_reviewers_on_a_project(cli: Typer, runner: CliRunner, environ: dict[str, str]) -> None:
    # Arrange
    respx.get(f"{PROJECT}/default-reviewers").mock(return_value=page([PROJECT_REVIEWER]))
    # Act
    listed = run(cli, runner, environ, "default-reviewer", "list", *SCOPE)
    effective = run(cli, runner, environ, "default-reviewer", "effective", *SCOPE)
    # Assert
    assert json.loads(listed.stdout)[0]["user"]["account_id"] == "a"
    assert effective.exit_code == ExitCode.USAGE


@respx.mock
def test_deploy_keys_on_a_repository(cli: Typer, runner: CliRunner, environ: dict[str, str]) -> None:
    # Arrange
    url = f"{BASE}/deploy-keys"
    respx.get(url).mock(return_value=page([KEY]))
    respx.get(f"{url}/9").mock(return_value=httpx.Response(200, json=KEY))
    created = respx.post(url).mock(return_value=httpx.Response(201, json=KEY))
    updated = respx.put(f"{url}/9").mock(return_value=httpx.Response(200, json=KEY))
    deleted = respx.delete(f"{url}/9").mock(return_value=httpx.Response(204))
    # Act
    listed = run(cli, runner, environ, "deploy-key", "list", *REPO)
    got = run(cli, runner, environ, "deploy-key", "get", "9", *REPO)
    create = run(cli, runner, environ, "deploy-key", "create", *REPO, "--key", "ssh-ed25519 AAA", "--label", "ci")
    update = run(cli, runner, environ, "deploy-key", "update", "9", *REPO, "--key", "ssh-ed25519 AAA", "--label", "x")
    delete = run(cli, runner, environ, "deploy-key", "delete", "9", *REPO, "--yes")
    # Assert
    assert json.loads(listed.stdout)[0]["id"] == 9
    assert json.loads(got.stdout)["label"] == "ci"
    assert body_of(created.calls.last.request) == {"key": "ssh-ed25519 AAA", "label": "ci"}
    assert body_of(updated.calls.last.request) == {"key": "ssh-ed25519 AAA", "label": "x"}
    assert create.exit_code == update.exit_code == delete.exit_code == ExitCode.OK
    assert deleted.called


@respx.mock
def test_deploy_keys_on_a_project(cli: Typer, runner: CliRunner, environ: dict[str, str]) -> None:
    # Arrange
    url = f"{PROJECT}/deploy-keys"
    respx.get(url).mock(return_value=page([KEY]))
    respx.post(url).mock(return_value=httpx.Response(201, json=KEY))
    # Act
    listed = run(cli, runner, environ, "deploy-key", "list", *SCOPE)
    create = run(cli, runner, environ, "deploy-key", "create", *SCOPE, "--key", "ssh-ed25519 AAA")
    update = run(cli, runner, environ, "deploy-key", "update", "9", *SCOPE, "--key", "ssh-ed25519 AAA")
    # Assert
    assert json.loads(listed.stdout)[0]["id"] == 9
    assert create.exit_code == ExitCode.OK
    assert update.exit_code == ExitCode.USAGE


@respx.mock
def test_permission_config_for_groups_and_users_on_a_repository(
    cli: Typer, runner: CliRunner, environ: dict[str, str]
) -> None:
    # Arrange
    groups = f"{BASE}/permissions-config/groups"
    users = f"{BASE}/permissions-config/users"
    respx.get(groups).mock(return_value=page([GROUP]))
    respx.get(f"{groups}/devs").mock(return_value=httpx.Response(200, json=GROUP))
    group_put = respx.put(f"{groups}/devs").mock(return_value=httpx.Response(200, json=GROUP))
    group_deleted = respx.delete(f"{groups}/devs").mock(return_value=httpx.Response(204))
    respx.get(users).mock(return_value=page([USER]))
    respx.get(f"{users}/a").mock(return_value=httpx.Response(200, json=USER))
    user_put = respx.put(f"{users}/a").mock(return_value=httpx.Response(200, json=USER))
    user_deleted = respx.delete(f"{users}/a").mock(return_value=httpx.Response(204))
    # Act
    group_list = run(cli, runner, environ, "permission-config", "group", "list", *REPO)
    group_get = run(cli, runner, environ, "permission-config", "group", "get", "devs", *REPO)
    group_set = run(cli, runner, environ, "permission-config", "group", "set", "devs", *REPO, "--permission", "write")
    group_delete = run(cli, runner, environ, "permission-config", "group", "delete", "devs", *REPO, "--yes")
    user_list = run(cli, runner, environ, "permission-config", "user", "list", *REPO)
    user_get = run(cli, runner, environ, "permission-config", "user", "get", "a", *REPO)
    user_set = run(cli, runner, environ, "permission-config", "user", "set", "a", *REPO, "--permission", "admin")
    user_delete = run(cli, runner, environ, "permission-config", "user", "delete", "a", *REPO, "--yes")
    # Assert
    assert json.loads(group_list.stdout)[0]["group"]["slug"] == "devs"
    assert json.loads(group_get.stdout)["permission"] == "write"
    assert body_of(group_put.calls.last.request) == {"permission": "write"}
    assert json.loads(user_list.stdout)[0]["permission"] == "admin"
    assert json.loads(user_get.stdout)["permission"] == "admin"
    assert body_of(user_put.calls.last.request) == {"permission": "admin"}
    assert group_set.exit_code == group_delete.exit_code == ExitCode.OK
    assert user_set.exit_code == user_delete.exit_code == ExitCode.OK
    assert group_deleted.called
    assert user_deleted.called


@respx.mock
def test_permission_config_on_a_project_accepts_create_repo(
    cli: Typer, runner: CliRunner, environ: dict[str, str]
) -> None:
    # Arrange
    route = respx.put(f"{PROJECT}/permissions-config/groups/devs").mock(return_value=httpx.Response(200, json=GROUP))
    # Act
    accepted = run(
        cli, runner, environ, "permission-config", "group", "set", "devs", *SCOPE, "--permission", "create-repo"
    )
    refused = run(
        cli, runner, environ, "permission-config", "group", "set", "devs", *REPO, "--permission", "create-repo"
    )
    # Assert
    assert accepted.exit_code == ExitCode.OK
    assert body_of(route.calls.last.request) == {"permission": "create-repo"}
    assert refused.exit_code == ExitCode.USAGE


@respx.mock
def test_permission_config_override_settings(cli: Typer, runner: CliRunner, environ: dict[str, str]) -> None:
    # Arrange
    state = {"type": "repository_inheritance_settings", "override_settings": {"branching_model": True}}
    respx.get(f"{BASE}/override-settings").mock(return_value=httpx.Response(200, json=state))
    updated = respx.put(f"{BASE}/override-settings").mock(return_value=httpx.Response(204))
    # Act
    shown = run(cli, runner, environ, "permission-config", "override", "show", *REPO)
    changed = run(
        cli,
        runner,
        environ,
        *["permission-config", "override", "set", *REPO, "--branching-model", "--inherit-branch-restrictions"],
        *["--merge-strategy"],
    )
    # Assert
    assert json.loads(shown.stdout)["override_settings"]["branching_model"] is True
    assert changed.exit_code == ExitCode.OK
    assert body_of(updated.calls.last.request) == {
        "override_settings": {"branching_model": True, "branch_restrictions": False, "default_merge_strategy": True}
    }


@respx.mock
def test_repo_property_commands(cli: Typer, runner: CliRunner, environ: dict[str, str]) -> None:
    # Arrange
    prop = f"{BASE}/properties/app/flag"
    respx.get(prop).mock(return_value=httpx.Response(200, json={"on": True}))
    stored = respx.put(prop).mock(return_value=httpx.Response(204))
    deleted = respx.delete(prop).mock(return_value=httpx.Response(204))
    # Act
    got = run(cli, runner, environ, "repo", "property", "get", "app", "flag", *REPO)
    set_value = run(cli, runner, environ, "repo", "property", "set", "app", "flag", "true", *REPO)
    delete = run(cli, runner, environ, "repo", "property", "delete", "app", "flag", *REPO)
    # Assert
    assert json.loads(got.stdout) == {"on": True}
    assert json.loads(stored.calls.last.request.content) is True
    assert set_value.exit_code == delete.exit_code == ExitCode.OK
    assert deleted.called

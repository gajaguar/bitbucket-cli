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
    from pathlib import Path

    import pytest
    from typer import Typer
    from typer.testing import CliRunner

BASE: Final = f"{REPOS}/widgets"
CONFIG: Final = f"{BASE}/pipelines_config"
REPO: Final = ["--repo", "widgets"]
PIPELINE: Final[dict[str, object]] = {
    "uuid": "{p}",
    "build_number": 12,
    "state": {"name": "COMPLETED", "result": {"name": "SUCCESSFUL"}},
    "target": {"ref_name": "main"},
}
STEP: Final[dict[str, object]] = {"uuid": "{s}", "state": {"name": "COMPLETED"}, "image": {"name": "python"}}
VARIABLE: Final[dict[str, object]] = {"uuid": "{v}", "key": "TOKEN", "value": "hunter2", "secured": False}
SCHEDULE: Final[dict[str, object]] = {"uuid": "{c}", "enabled": True, "cron_pattern": "0 0 12 * * ? *"}
HOST: Final[dict[str, object]] = {"uuid": "{h}", "hostname": "git.test", "public_key": {"key_type": "ssh-ed25519"}}
RUNNER: Final[dict[str, object]] = {
    "uuid": "{r}",
    "name": "builder",
    "oauth_client": {"id": "cid", "secret": "top-secret"},
}
CACHE: Final[dict[str, object]] = {"uuid": "{k}", "name": "pip", "path": "/c"}


@respx.mock
def test_pipeline_list_get_steps_and_stop(cli: Typer, runner: CliRunner, environ: dict[str, str]) -> None:
    # Arrange
    listing = respx.get(f"{BASE}/pipelines").mock(return_value=page([PIPELINE]))
    respx.get(f"{BASE}/pipelines/{{p}}").mock(return_value=httpx.Response(200, json=PIPELINE))
    respx.get(f"{BASE}/pipelines/{{p}}/steps").mock(return_value=page([STEP]))
    respx.get(f"{BASE}/pipelines/{{p}}/steps/{{s}}").mock(return_value=httpx.Response(200, json=STEP))
    stopped = respx.post(f"{BASE}/pipelines/{{p}}/stopPipeline").mock(return_value=httpx.Response(204))
    # Act
    listed = run(
        cli,
        runner,
        environ,
        *["pipeline", "list", *REPO, "--branch", "main", "--tag", "v1", "--status", "x", "--sort", "-created_on"],
        *["--filter", "creator.uuid={u}"],
    )
    got = run(cli, runner, environ, "pipeline", "get", "{p}", *REPO)
    steps = run(cli, runner, environ, "pipeline", "steps", "{p}", *REPO)
    step = run(cli, runner, environ, "pipeline", "step", "{p}", "{s}", *REPO)
    stop = run(cli, runner, environ, "pipeline", "stop", "{p}", *REPO)
    # Assert
    assert json.loads(listed.stdout)[0]["build_number"] == 12
    assert dict(listing.calls.last.request.url.params) == {
        "sort": "-created_on",
        "status": "x",
        "target.branch": "main",
        "target.tag": "v1",
        "creator.uuid": "{u}",
    }
    assert json.loads(got.stdout)["uuid"] == "{p}"
    assert json.loads(steps.stdout)[0]["uuid"] == "{s}"
    assert json.loads(step.stdout)["image"]["name"] == "python"
    assert stop.exit_code == ExitCode.OK
    assert stopped.called


def test_pipeline_list_rejects_a_malformed_filter(cli: Typer, runner: CliRunner, environ: dict[str, str]) -> None:
    # Arrange
    arguments = ["pipeline", "list", *REPO, "--filter", "nonsense"]
    # Act
    result = run(cli, runner, environ, *arguments)
    # Assert
    assert result.exit_code == ExitCode.USAGE


@respx.mock
def test_pipeline_run_on_a_branch_with_variables_from_the_environment(
    cli: Typer, runner: CliRunner, environ: dict[str, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    # Arrange
    monkeypatch.setenv("DEPLOY_ENV", "prod")
    monkeypatch.setenv("API_TOKEN", "token-value")
    route = respx.post(f"{BASE}/pipelines").mock(return_value=httpx.Response(201, json=PIPELINE))
    # Act
    result = run(
        cli,
        runner,
        environ,
        *["pipeline", "run", *REPO, "--branch", "main", "--commit", "abc", "--custom", "deploy"],
        *["--variable-env", "DEPLOY_ENV", "--secured-variable-env", "API_TOKEN", "--merge-defaults"],
        *["--create-branch", "tmp"],
    )
    # Assert
    assert result.exit_code == ExitCode.OK
    assert body_of(route.calls.last.request) == {
        "target": {
            "type": "pipeline_ref_target",
            "ref_type": "branch",
            "ref_name": "main",
            "commit": {"type": "commit", "hash": "abc"},
            "selector": {"type": "custom", "pattern": "deploy"},
        },
        "variables": [
            {"key": "DEPLOY_ENV", "value": "prod"},
            {"key": "API_TOKEN", "value": "token-value", "secured": True},
        ],
    }
    assert dict(route.calls.last.request.url.params) == {"merge_defaults": "true", "target_branch_to_create": "tmp"}
    assert "token-value" not in result.stdout


@respx.mock
def test_pipeline_run_on_a_tag_and_on_a_commit(cli: Typer, runner: CliRunner, environ: dict[str, str]) -> None:
    # Arrange
    route = respx.post(f"{BASE}/pipelines").mock(return_value=httpx.Response(201, json=PIPELINE))
    # Act
    tag = run(cli, runner, environ, "pipeline", "run", *REPO, "--tag", "v1")
    commit = run(cli, runner, environ, "pipeline", "run", *REPO, "--commit", "abc")
    # Assert
    assert tag.exit_code == commit.exit_code == ExitCode.OK
    assert body_of(route.calls[0].request)["target"]["ref_type"] == "tag"  # type: ignore[index]
    assert body_of(route.calls[1].request)["target"]["type"] == "pipeline_commit_target"  # type: ignore[index]


def test_pipeline_run_needs_a_target_and_every_named_variable(
    cli: Typer, runner: CliRunner, environ: dict[str, str]
) -> None:
    # Arrange
    missing_variable = ["pipeline", "run", *REPO, "--branch", "main", "--variable-env", "NOT_SET_ANYWHERE"]
    # Act
    no_target = run(cli, runner, environ, "pipeline", "run", *REPO)
    unset = run(cli, runner, environ, *missing_variable)
    # Assert
    assert no_target.exit_code == ExitCode.USAGE
    assert unset.exit_code == ExitCode.USAGE


@respx.mock
def test_pipeline_logs_and_test_reports(cli: Typer, runner: CliRunner, environ: dict[str, str]) -> None:
    # Arrange
    step = f"{BASE}/pipelines/{{p}}/steps/{{s}}"
    log = respx.get(f"{step}/log").mock(return_value=httpx.Response(200, content=b"building\n"))
    respx.get(f"{step}/logs/{{l}}").mock(return_value=httpx.Response(200, content=b"service\n"))
    respx.get(f"{step}/test_reports").mock(return_value=httpx.Response(200, json={"total": 3}))
    respx.get(f"{step}/test_reports/test_cases").mock(return_value=httpx.Response(200, json=[{"uuid": "{t}"}]))
    respx.get(f"{step}/test_reports/test_cases/{{t}}/test_case_reasons").mock(
        return_value=httpx.Response(200, json=[{"message": "boom"}])
    )
    # Act
    output = run(cli, runner, environ, "pipeline", "log", "{p}", "{s}", *REPO, "--start", "0", "--end", "99")
    container = run(cli, runner, environ, "pipeline", "log", "{p}", "{s}", *REPO, "--container", "{l}")
    tests = run(cli, runner, environ, "pipeline", "tests", "{p}", "{s}", *REPO)
    cases = run(cli, runner, environ, "pipeline", "test-cases", "{p}", "{s}", *REPO)
    reasons = run(cli, runner, environ, "pipeline", "test-case-reasons", "{p}", "{s}", "{t}", *REPO)
    # Assert
    assert output.stdout_bytes == b"building\n"
    assert log.calls.last.request.headers["Range"] == "bytes=0-99"
    assert container.stdout_bytes == b"service\n"
    assert json.loads(tests.stdout) == {"total": 3}
    assert json.loads(cases.stdout)[0]["uuid"] == "{t}"
    assert json.loads(reasons.stdout)[0]["message"] == "boom"


@respx.mock
def test_pipeline_config_commands(cli: Typer, runner: CliRunner, environ: dict[str, str]) -> None:
    # Arrange
    state = {"enabled": True, "repository": {"full_name": "acme/widgets"}}
    respx.get(CONFIG).mock(return_value=httpx.Response(200, json=state))
    updated = respx.put(CONFIG).mock(return_value=httpx.Response(200, json=state))
    number = respx.put(f"{CONFIG}/build_number").mock(return_value=httpx.Response(200, json={"next": 50}))
    # Act
    got = run(cli, runner, environ, "pipeline", "config", "get", *REPO)
    update = run(cli, runner, environ, "pipeline", "config", "update", *REPO, "--disabled")
    build_number = run(cli, runner, environ, "pipeline", "config", "build-number", *REPO, "--next", "50")
    # Assert
    assert json.loads(got.stdout)["enabled"] is True
    assert body_of(updated.calls.last.request) == {"enabled": False}
    assert update.exit_code == ExitCode.OK
    assert body_of(number.calls.last.request) == {"next": 50}
    assert json.loads(build_number.stdout)["next"] == 50


@respx.mock
def test_pipeline_ssh_key_pair_commands_read_the_secret_from_a_file_or_stdin(
    cli: Typer, runner: CliRunner, environ: dict[str, str], tmp_path: Path
) -> None:
    # Arrange
    url = f"{CONFIG}/ssh/key_pair"
    pair = {"public_key": "ssh-ed25519 PUB", "private_key": "hidden"}
    respx.get(url).mock(return_value=httpx.Response(200, json=pair))
    put = respx.put(url).mock(return_value=httpx.Response(200, json=pair))
    deleted = respx.delete(url).mock(return_value=httpx.Response(204))
    private = tmp_path / "id"
    private.write_text("PRIVATE-FROM-FILE")
    # Act
    got = run(cli, runner, environ, "pipeline", "ssh-key", "get", *REPO)
    from_file = run(
        cli, runner, environ, *["pipeline", "ssh-key", "set", *REPO, "--private-key-file", str(private)], output="json"
    )
    from_stdin = run(
        cli,
        runner,
        environ,
        "pipeline",
        "ssh-key",
        "set",
        *REPO,
        "--stdin",
        "--public-key",
        "PUB",
        stdin="PRIVATE-STDIN\n",
    )
    delete = run(cli, runner, environ, "pipeline", "ssh-key", "delete", *REPO, "--yes")
    # Assert
    assert json.loads(got.stdout)["public_key"] == "ssh-ed25519 PUB"
    assert body_of(put.calls[0].request) == {"private_key": "PRIVATE-FROM-FILE"}
    assert body_of(put.calls[1].request) == {"private_key": "PRIVATE-STDIN", "public_key": "PUB"}
    assert "PRIVATE" not in from_file.stdout + from_stdin.stdout + got.stdout
    assert "hidden" not in got.stdout
    assert delete.exit_code == ExitCode.OK
    assert deleted.called


def test_pipeline_ssh_key_set_fails_without_a_file_stdin_or_terminal(
    cli: Typer, runner: CliRunner, environ: dict[str, str], tmp_path: Path
) -> None:
    # Arrange
    arguments = ["pipeline", "ssh-key", "set", *REPO, "--private-key-file", str(tmp_path / "missing")]
    # Act
    unreadable = run(cli, runner, environ, *arguments)
    no_input = run(cli, runner, environ, "pipeline", "ssh-key", "set", *REPO)
    # Assert
    assert unreadable.exit_code == ExitCode.USAGE
    assert no_input.exit_code == ExitCode.USAGE


@respx.mock
def test_pipeline_known_host_commands(cli: Typer, runner: CliRunner, environ: dict[str, str]) -> None:
    # Arrange
    url = f"{CONFIG}/ssh/known_hosts"
    respx.get(url).mock(return_value=page([HOST]))
    respx.get(f"{url}/{{h}}").mock(return_value=httpx.Response(200, json=HOST))
    created = respx.post(url).mock(return_value=httpx.Response(201, json=HOST))
    updated = respx.put(f"{url}/{{h}}").mock(return_value=httpx.Response(200, json=HOST))
    deleted = respx.delete(f"{url}/{{h}}").mock(return_value=httpx.Response(204))
    # Act
    listed = run(cli, runner, environ, "pipeline", "known-host", "list", *REPO)
    got = run(cli, runner, environ, "pipeline", "known-host", "get", "{h}", *REPO)
    create = run(
        cli,
        runner,
        environ,
        *["pipeline", "known-host", "create", *REPO, "--hostname", "git.test", "--key-type", "ssh-ed25519"],
        *["--key", "AAAA"],
    )
    update = run(cli, runner, environ, "pipeline", "known-host", "update", "{h}", *REPO, "--hostname", "new.test")
    delete = run(cli, runner, environ, "pipeline", "known-host", "delete", "{h}", *REPO, "--yes")
    # Assert
    assert json.loads(listed.stdout)[0]["hostname"] == "git.test"
    assert json.loads(got.stdout)["uuid"] == "{h}"
    assert body_of(created.calls.last.request) == {
        "hostname": "git.test",
        "public_key": {"key_type": "ssh-ed25519", "key": "AAAA"},
    }
    assert body_of(updated.calls.last.request) == {"hostname": "new.test"}
    assert create.exit_code == update.exit_code == delete.exit_code == ExitCode.OK
    assert deleted.called


@respx.mock
def test_pipeline_cache_commands(cli: Typer, runner: CliRunner, environ: dict[str, str]) -> None:
    # Arrange
    url = f"{BASE}/pipelines-config/caches"
    respx.get(url).mock(return_value=page([CACHE]))
    respx.get(f"{url}/{{k}}/content-uri").mock(return_value=httpx.Response(200, json={"uri": "https://c.test"}))
    deleted = respx.delete(f"{url}/{{k}}").mock(return_value=httpx.Response(204))
    by_name = respx.delete(url).mock(return_value=httpx.Response(204))
    # Act
    listed = run(cli, runner, environ, "pipeline", "cache", "list", *REPO)
    uri = run(cli, runner, environ, "pipeline", "cache", "uri", "{k}", *REPO)
    delete = run(cli, runner, environ, "pipeline", "cache", "delete", "{k}", *REPO, "--yes")
    delete_named = run(cli, runner, environ, "pipeline", "cache", "delete-by-name", "pip", *REPO, "--yes")
    # Assert
    assert json.loads(listed.stdout)[0]["name"] == "pip"
    assert json.loads(uri.stdout)["uri"] == "https://c.test"
    assert delete.exit_code == delete_named.exit_code == ExitCode.OK
    assert deleted.called
    assert by_name.calls.last.request.url.params["name"] == "pip"


@respx.mock
def test_pipeline_variables_never_print_values_and_read_them_from_stdin(
    cli: Typer, runner: CliRunner, environ: dict[str, str]
) -> None:
    # Arrange
    url = f"{CONFIG}/variables"
    respx.get(url).mock(return_value=page([VARIABLE]))
    respx.get(f"{url}/{{v}}").mock(return_value=httpx.Response(200, json=VARIABLE))
    created = respx.post(url).mock(return_value=httpx.Response(201, json=VARIABLE))
    updated = respx.put(f"{url}/{{v}}").mock(return_value=httpx.Response(200, json=VARIABLE))
    deleted = respx.delete(f"{url}/{{v}}").mock(return_value=httpx.Response(204))
    # Act
    listed = run(cli, runner, environ, "pipeline", "variable", "list", *REPO)
    got = run(cli, runner, environ, "pipeline", "variable", "get", "{v}", *REPO)
    create = run(
        cli, runner, environ, "pipeline", "variable", "create", "TOKEN", *REPO, "--stdin", "--secured", stdin="v1\n"
    )
    rename = run(cli, runner, environ, "pipeline", "variable", "update", "{v}", *REPO, "--key", "NEW", "--unsecured")
    revalue = run(cli, runner, environ, "pipeline", "variable", "update", "{v}", *REPO, "--stdin", stdin="v2")
    delete = run(cli, runner, environ, "pipeline", "variable", "delete", "{v}", *REPO, "--yes")
    # Assert
    assert "hunter2" not in listed.stdout + got.stdout + create.stdout
    assert json.loads(listed.stdout)[0]["key"] == "TOKEN"
    assert body_of(created.calls.last.request) == {"key": "TOKEN", "value": "v1", "secured": True}
    assert body_of(updated.calls[0].request) == {"key": "NEW", "secured": False}
    assert body_of(updated.calls[1].request) == {"value": "v2"}
    assert rename.exit_code == revalue.exit_code == delete.exit_code == ExitCode.OK
    assert deleted.called


@respx.mock
def test_pipeline_variables_of_the_workspace_when_no_repository_is_given(
    cli: Typer, runner: CliRunner, environ: dict[str, str]
) -> None:
    # Arrange
    route = respx.get(f"{WORKSPACE}/pipelines-config/variables").mock(return_value=page([VARIABLE]))
    # Act
    result = run(cli, runner, environ, "pipeline", "variable", "list")
    # Assert
    assert json.loads(result.stdout)[0]["key"] == "TOKEN"
    assert route.called


def test_pipeline_variable_create_without_stdin_or_a_terminal_fails(
    cli: Typer, runner: CliRunner, environ: dict[str, str]
) -> None:
    # Arrange
    arguments = ["pipeline", "variable", "create", "TOKEN", *REPO]
    # Act
    result = run(cli, runner, environ, *arguments)
    # Assert
    assert result.exit_code == ExitCode.USAGE
    assert "--stdin" in result.stderr


@respx.mock
def test_pipeline_variable_create_prompts_for_a_hidden_value_on_a_terminal(
    cli: Typer, runner: CliRunner, environ: dict[str, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    # Arrange
    monkeypatch.setattr("bitbucket_unofficial_cli.services.secrets._interactive", lambda: True)
    created = respx.post(f"{CONFIG}/variables").mock(return_value=httpx.Response(201, json=VARIABLE))
    # Act
    result = run(cli, runner, environ, "pipeline", "variable", "create", "TOKEN", *REPO, stdin="typed\n")
    # Assert
    assert result.exit_code == ExitCode.OK
    assert body_of(created.calls.last.request)["value"] == "typed"
    assert "typed" not in result.stdout


@respx.mock
def test_pipeline_schedule_commands(cli: Typer, runner: CliRunner, environ: dict[str, str]) -> None:
    # Arrange
    url = f"{CONFIG}/schedules"
    respx.get(url).mock(return_value=page([SCHEDULE]))
    respx.get(f"{url}/{{c}}").mock(return_value=httpx.Response(200, json=SCHEDULE))
    created = respx.post(url).mock(return_value=httpx.Response(201, json=SCHEDULE))
    updated = respx.put(f"{url}/{{c}}").mock(return_value=httpx.Response(200, json=SCHEDULE))
    deleted = respx.delete(f"{url}/{{c}}").mock(return_value=httpx.Response(204))
    respx.get(f"{url}/{{c}}/executions").mock(
        return_value=page([{"type": "pipeline_schedule_execution_executed", "pipeline": PIPELINE}])
    )
    # Act
    listed = run(cli, runner, environ, "pipeline", "schedule", "list", *REPO)
    got = run(cli, runner, environ, "pipeline", "schedule", "get", "{c}", *REPO)
    create = run(
        cli,
        runner,
        environ,
        *["pipeline", "schedule", "create", *REPO, "--ref-name", "main", "--pattern", "nightly"],
        *["--cron", "0 0 12 * * ? *", "--enabled"],
    )
    update = run(cli, runner, environ, "pipeline", "schedule", "update", "{c}", *REPO, "--disabled")
    delete = run(cli, runner, environ, "pipeline", "schedule", "delete", "{c}", *REPO, "--yes")
    executions = run(cli, runner, environ, "pipeline", "schedule", "executions", "{c}", *REPO)
    # Assert
    assert json.loads(listed.stdout)[0]["uuid"] == "{c}"
    assert json.loads(got.stdout)["cron_pattern"] == "0 0 12 * * ? *"
    assert body_of(created.calls.last.request) == {
        "target": {
            "type": "pipeline_ref_target",
            "ref_type": "branch",
            "ref_name": "main",
            "selector": {"type": "custom", "pattern": "nightly"},
        },
        "cron_pattern": "0 0 12 * * ? *",
        "enabled": True,
    }
    assert body_of(updated.calls.last.request) == {"enabled": False}
    assert create.exit_code == update.exit_code == delete.exit_code == ExitCode.OK
    assert json.loads(executions.stdout)[0]["pipeline"]["build_number"] == 12
    assert deleted.called


@respx.mock
def test_pipeline_runner_commands_on_a_repository_and_on_the_workspace(
    cli: Typer, runner: CliRunner, environ: dict[str, str]
) -> None:
    # Arrange
    respx.get(f"{BASE}/pipelines-config/runners").mock(return_value=page([RUNNER]))
    respx.get(f"{WORKSPACE}/pipelines-config/runners/{{r}}").mock(return_value=httpx.Response(200, json=RUNNER))
    created = respx.post(f"{WORKSPACE}/pipelines-config/runners").mock(return_value=httpx.Response(201, json=RUNNER))
    updated = respx.put(f"{BASE}/pipelines-config/runners/{{r}}").mock(return_value=httpx.Response(200, json=RUNNER))
    deleted = respx.delete(f"{WORKSPACE}/pipelines-config/runners/{{r}}").mock(return_value=httpx.Response(204))
    # Act
    listed = run(cli, runner, environ, "pipeline", "runner", "list", *REPO)
    got = run(cli, runner, environ, "pipeline", "runner", "get", "{r}")
    create = run(cli, runner, environ, "pipeline", "runner", "create", "--name", "builder", "--label", "linux")
    update = run(cli, runner, environ, "pipeline", "runner", "update", "{r}", *REPO, "--name", "renamed")
    delete = run(cli, runner, environ, "pipeline", "runner", "delete", "{r}", "--yes")
    # Assert
    assert json.loads(listed.stdout)[0]["name"] == "builder"
    assert json.loads(got.stdout)["uuid"] == "{r}"
    assert body_of(created.calls.last.request) == {"name": "builder", "labels": ["linux"]}
    assert body_of(updated.calls.last.request) == {"name": "renamed"}
    assert "top-secret" not in listed.stdout + got.stdout + create.stdout
    assert create.exit_code == update.exit_code == delete.exit_code == ExitCode.OK
    assert deleted.called


@respx.mock
def test_workspace_oidc_commands_print_json(cli: Typer, runner: CliRunner, environ: dict[str, str]) -> None:
    # Arrange
    oidc = f"{WORKSPACE}/pipelines-config/identity/oidc"
    respx.get(f"{oidc}/.well-known/openid-configuration").mock(return_value=httpx.Response(200, json={"issuer": "i"}))
    respx.get(f"{oidc}/keys.json").mock(return_value=httpx.Response(200, json={"keys": []}))
    # Act
    configuration = run(cli, runner, environ, "workspace", "oidc-configuration")
    keys = run(cli, runner, environ, "workspace", "oidc-keys")
    # Assert
    assert json.loads(configuration.stdout) == {"issuer": "i"}
    assert json.loads(keys.stdout) == {"keys": []}

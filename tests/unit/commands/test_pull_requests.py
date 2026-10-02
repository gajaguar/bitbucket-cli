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
    from typer import Typer
    from typer.testing import CliRunner

PRS: Final = f"{REPOS}/widgets/pullrequests"
PR: Final[dict[str, object]] = {
    "type": "pullrequest",
    "id": 7,
    "title": "Fix it",
    "state": "OPEN",
    "author": {"display_name": "Some One"},
    "source": {"branch": {"name": "feature"}},
    "destination": {"branch": {"name": "main"}},
}
ACCOUNT: Final[dict[str, object]] = {"display_name": "Some One", "account_id": "a"}
COMMENT: Final[dict[str, object]] = {"id": 3, "content": {"raw": "hi"}, "user": ACCOUNT}
TASK: Final[dict[str, object]] = {"id": 4, "state": "UNRESOLVED", "content": {"raw": "do"}}
REPO: Final = ["--repo", "widgets"]


@respx.mock
def test_pr_list_filters_by_state_and_query(cli: Typer, runner: CliRunner, environ: dict[str, str]) -> None:
    # Arrange
    route = respx.get(PRS).mock(return_value=page([PR]))
    # Act
    result = run(cli, runner, environ, *["pr", "list", *REPO, "--state", "OPEN", "--state", "DRAFT", "-q", "x"])
    # Assert
    assert json.loads(result.stdout)[0]["id"] == 7
    assert route.calls.last.request.url.params.get_list("state") == ["OPEN", "DRAFT"]
    assert route.calls.last.request.url.params["q"] == "x"


@respx.mock
def test_pr_list_reads_one_page_from_a_cursor(cli: Typer, runner: CliRunner, environ: dict[str, str]) -> None:
    # Arrange
    cursor = f"{PRS}?page=2"
    respx.get(cursor).mock(return_value=page([PR], next_url=f"{PRS}?page=3"))
    # Act
    result = run(cli, runner, environ, *["pr", "list", *REPO, "--cursor", cursor])
    # Assert
    assert result.exit_code == ExitCode.OK
    assert "next cursor" in result.stderr


@respx.mock
def test_pr_by_author(cli: Typer, runner: CliRunner, environ: dict[str, str]) -> None:
    # Arrange
    route = respx.get(f"{WORKSPACE}/pullrequests/557058:abc").mock(return_value=page([PR]))
    # Act
    result = run(cli, runner, environ, "pr", "by-author", "557058:abc", "--state", "MERGED")
    # Assert
    assert json.loads(result.stdout)[0]["id"] == 7
    assert route.calls.last.request.url.params["state"] == "MERGED"


@respx.mock
def test_pr_get_create_and_update(cli: Typer, runner: CliRunner, environ: dict[str, str]) -> None:
    # Arrange
    respx.get(f"{PRS}/7").mock(return_value=httpx.Response(200, json=PR))
    created = respx.post(PRS).mock(return_value=httpx.Response(201, json=PR))
    updated = respx.put(f"{PRS}/7").mock(return_value=httpx.Response(200, json=PR))
    # Act
    got = run(cli, runner, environ, "pr", "get", "7", *REPO)
    create = run(
        cli,
        runner,
        environ,
        *["pr", "create", *REPO, "--title", "Fix it", "--source", "feature", "--destination", "main"],
        *["--reviewer", "{u}", "--close-source-branch", "--description", "d"],
    )
    update = run(cli, runner, environ, "pr", "update", "7", *REPO, "--title", "New", "--destination", "dev")
    # Assert
    assert json.loads(got.stdout)["title"] == "Fix it"
    assert create.exit_code == update.exit_code == ExitCode.OK
    assert body_of(created.calls.last.request) == {
        "title": "Fix it",
        "source": {"branch": {"name": "feature"}},
        "destination": {"branch": {"name": "main"}},
        "description": "d",
        "reviewers": [{"uuid": "{u}"}],
        "close_source_branch": True,
    }
    assert body_of(updated.calls.last.request) == {"title": "New", "destination": {"branch": {"name": "dev"}}}


@respx.mock
def test_pr_review_actions(cli: Typer, runner: CliRunner, environ: dict[str, str]) -> None:
    # Arrange
    respx.post(f"{PRS}/7/approve").mock(return_value=httpx.Response(200, json=ACCOUNT))
    respx.delete(f"{PRS}/7/approve").mock(return_value=httpx.Response(204))
    respx.post(f"{PRS}/7/request-changes").mock(return_value=httpx.Response(200, json=ACCOUNT))
    respx.delete(f"{PRS}/7/request-changes").mock(return_value=httpx.Response(204))
    respx.post(f"{PRS}/7/decline").mock(return_value=httpx.Response(200, json=PR))
    # Act
    results = [
        run(cli, runner, environ, "pr", verb, "7", *REPO)
        for verb in ("approve", "unapprove", "request-changes", "unrequest-changes", "decline")
    ]
    # Assert
    assert [result.exit_code for result in results] == [ExitCode.OK] * 5


@respx.mock
def test_pr_merge_returns_the_task(cli: Typer, runner: CliRunner, environ: dict[str, str]) -> None:
    # Arrange
    route = respx.post(f"{PRS}/7/merge").mock(return_value=httpx.Response(202, json={"task_id": "t1"}))
    # Act
    result = run(
        cli,
        runner,
        environ,
        *["pr", "merge", "7", *REPO, "-m", "msg", "--strategy", "squash", "--keep-source-branch"],
    )
    # Assert
    assert json.loads(result.stdout)["task_id"] == "t1"
    assert body_of(route.calls.last.request) == {
        "message": "msg",
        "merge_strategy": "squash",
        "close_source_branch": False,
    }


@respx.mock
def test_pr_merge_waits_for_the_task(cli: Typer, runner: CliRunner, environ: dict[str, str]) -> None:
    # Arrange
    respx.post(f"{PRS}/7/merge").mock(return_value=httpx.Response(202, json={"task_id": "t1"}))
    respx.get(f"{PRS}/7/merge/task-status/t1").mock(
        return_value=httpx.Response(200, json={"task_status": "SUCCESS", "pull_request": PR})
    )
    # Act
    result = run(cli, runner, environ, "pr", "merge", "7", *REPO, "--wait", "--timeout", "5")
    # Assert
    assert json.loads(result.stdout)["task_status"] == "SUCCESS"


@respx.mock
def test_pr_merge_status_and_checks(cli: Typer, runner: CliRunner, environ: dict[str, str]) -> None:
    # Arrange
    respx.get(f"{PRS}/7/merge/task-status/t1").mock(return_value=httpx.Response(200, json={"task_status": "PENDING"}))
    respx.get(f"{PRS}/7/mergeability/checks").mock(
        return_value=page([{"type": "git_mergeability_check", "status": "PASSED", "uuid": "c1"}])
    )
    # Act
    status = run(cli, runner, environ, "pr", "merge-status", "7", "t1", *REPO)
    checks = run(cli, runner, environ, "pr", "checks", "7", *REPO, "-q", "x")
    # Assert
    assert json.loads(status.stdout)["task_status"] == "PENDING"
    assert json.loads(checks.stdout)[0]["status"] == "PASSED"


@respx.mock
def test_pr_raw_text_commands_print_the_body_unchanged(cli: Typer, runner: CliRunner, environ: dict[str, str]) -> None:
    # Arrange
    respx.get(f"{PRS}/7/diff").mock(return_value=httpx.Response(200, text="diff --git a b\n"))
    respx.get(f"{PRS}/7/patch").mock(return_value=httpx.Response(200, text="From abc"))
    # Act
    diff = run(cli, runner, environ, "pr", "diff", "7", *REPO)
    patch = run(cli, runner, environ, "pr", "patch", "7", *REPO)
    # Assert
    assert diff.stdout == "diff --git a b\n"
    assert patch.stdout == "From abc\n"


@respx.mock
def test_pr_listings(cli: Typer, runner: CliRunner, environ: dict[str, str]) -> None:
    # Arrange
    respx.get(f"{PRS}/7/diffstat").mock(return_value=page([{"status": "modified", "new": {"path": "a.py"}}]))
    respx.get(f"{PRS}/7/commits").mock(return_value=page([{"hash": "abc", "message": "m"}]))
    respx.get(f"{PRS}/7/conflicts").mock(return_value=page([{"path": "a.py", "scenario": "content"}]))
    respx.get(f"{PRS}/7/activity").mock(return_value=page([{"approval": {"user": ACCOUNT}}]))
    respx.get(f"{REPOS}/widgets/pullrequests/activity").mock(return_value=page([{"update": {"state": "OPEN"}}]))
    # Act
    files = run(cli, runner, environ, "pr", "files", "7", *REPO)
    commits = run(cli, runner, environ, "pr", "commits", "7", *REPO)
    conflicts = run(cli, runner, environ, "pr", "conflicts", "7", *REPO)
    one = run(cli, runner, environ, "pr", "activity", "7", *REPO)
    every = run(cli, runner, environ, "pr", "activity", *REPO)
    # Assert
    assert json.loads(files.stdout)[0]["new"]["path"] == "a.py"
    assert json.loads(commits.stdout)[0]["hash"] == "abc"
    assert json.loads(conflicts.stdout)[0]["scenario"] == "content"
    assert "approval" in json.loads(one.stdout)[0]
    assert json.loads(every.stdout)[0]["update"]["state"] == "OPEN"


@respx.mock
def test_pr_comment_commands(cli: Typer, runner: CliRunner, environ: dict[str, str]) -> None:
    # Arrange
    base = f"{PRS}/7/comments"
    respx.get(base).mock(return_value=page([COMMENT]))
    respx.get(f"{base}/3").mock(return_value=httpx.Response(200, json=COMMENT))
    created = respx.post(base).mock(return_value=httpx.Response(201, json=COMMENT))
    updated = respx.put(f"{base}/3").mock(return_value=httpx.Response(200, json=COMMENT))
    deleted = respx.delete(f"{base}/3").mock(return_value=httpx.Response(204))
    respx.post(f"{base}/3/resolve").mock(return_value=httpx.Response(200, json=COMMENT))
    unresolved = respx.delete(f"{base}/3/resolve").mock(return_value=httpx.Response(204))
    # Act
    listed = run(cli, runner, environ, "pr", "comment", "list", "7", *REPO)
    got = run(cli, runner, environ, "pr", "comment", "get", "7", "3", *REPO)
    create = run(
        cli,
        runner,
        environ,
        *["pr", "comment", "create", "7", *REPO, "-m", "hi", "--inline-path", "a.py", "--inline-to", "4"],
        *["--parent", "2"],
    )
    update = run(cli, runner, environ, "pr", "comment", "update", "7", "3", *REPO, "-m", "bye")
    resolve = run(cli, runner, environ, "pr", "comment", "resolve", "7", "3", *REPO)
    unresolve = run(cli, runner, environ, "pr", "comment", "unresolve", "7", "3", *REPO)
    delete = run(cli, runner, environ, "pr", "comment", "delete", "7", "3", *REPO, "--yes")
    # Assert
    assert json.loads(listed.stdout)[0]["id"] == 3
    assert json.loads(got.stdout)["content"]["raw"] == "hi"
    assert body_of(created.calls.last.request) == {
        "content": {"raw": "hi"},
        "inline": {"path": "a.py", "to": 4},
        "parent": {"id": 2},
    }
    assert body_of(updated.calls.last.request) == {"content": {"raw": "bye"}}
    assert create.exit_code == update.exit_code == resolve.exit_code == ExitCode.OK
    assert unresolve.exit_code == delete.exit_code == ExitCode.OK
    assert deleted.called
    assert unresolved.called


@respx.mock
def test_pr_task_commands(cli: Typer, runner: CliRunner, environ: dict[str, str]) -> None:
    # Arrange
    base = f"{PRS}/7/tasks"
    respx.get(base).mock(return_value=page([TASK]))
    respx.get(f"{base}/4").mock(return_value=httpx.Response(200, json=TASK))
    created = respx.post(base).mock(return_value=httpx.Response(201, json=TASK))
    updated = respx.put(f"{base}/4").mock(return_value=httpx.Response(200, json=TASK))
    deleted = respx.delete(f"{base}/4").mock(return_value=httpx.Response(204))
    # Act
    listed = run(cli, runner, environ, "pr", "task", "list", "7", *REPO)
    got = run(cli, runner, environ, "pr", "task", "get", "7", "4", *REPO)
    create = run(cli, runner, environ, "pr", "task", "create", "7", *REPO, "-m", "do", "--pending")
    update = run(cli, runner, environ, "pr", "task", "update", "7", "4", *REPO, "--state", "RESOLVED")
    delete = run(cli, runner, environ, "pr", "task", "delete", "7", "4", *REPO, "--yes")
    # Assert
    assert json.loads(listed.stdout)[0]["id"] == 4
    assert json.loads(got.stdout)["state"] == "UNRESOLVED"
    assert body_of(created.calls.last.request) == {"content": {"raw": "do"}, "pending": True}
    assert body_of(updated.calls.last.request) == {"state": "RESOLVED"}
    assert create.exit_code == update.exit_code == delete.exit_code == ExitCode.OK
    assert deleted.called


@respx.mock
def test_pr_status_and_property_commands(cli: Typer, runner: CliRunner, environ: dict[str, str]) -> None:
    # Arrange
    respx.get(f"{PRS}/7/statuses").mock(return_value=page([{"key": "ci", "state": "SUCCESSFUL"}]))
    prop = f"{PRS}/7/properties/app/flag"
    respx.get(prop).mock(return_value=httpx.Response(200, json={"on": True}))
    stored = respx.put(prop).mock(return_value=httpx.Response(204))
    deleted = respx.delete(prop).mock(return_value=httpx.Response(204))
    # Act
    statuses = run(cli, runner, environ, "pr", "status", "list", "7", *REPO)
    got = run(cli, runner, environ, "pr", "property", "get", "7", "app", "flag", *REPO)
    set_inline = run(cli, runner, environ, "pr", "property", "set", "7", "app", "flag", '{"on": false}', *REPO)
    set_stdin = run(cli, runner, environ, "pr", "property", "set", "7", "app", "flag", "-", *REPO, stdin="[1]")
    delete = run(cli, runner, environ, "pr", "property", "delete", "7", "app", "flag", *REPO)
    # Assert
    assert json.loads(statuses.stdout)[0]["key"] == "ci"
    assert json.loads(got.stdout) == {"on": True}
    assert set_inline.exit_code == set_stdin.exit_code == delete.exit_code == ExitCode.OK
    assert json.loads(stored.calls.last.request.content) == [1]
    assert deleted.called


def test_pr_property_set_rejects_invalid_json(cli: Typer, runner: CliRunner, environ: dict[str, str]) -> None:
    # Arrange
    arguments = ["pr", "property", "set", "7", "app", "flag", "{nope", *REPO]
    # Act
    result = run(cli, runner, environ, *arguments)
    # Assert
    assert result.exit_code == ExitCode.USAGE


@respx.mock
def test_pr_comment_create_without_a_position_sends_only_the_text(
    cli: Typer, runner: CliRunner, environ: dict[str, str]
) -> None:
    # Arrange
    route = respx.post(f"{PRS}/7/comments").mock(return_value=httpx.Response(201, json=COMMENT))
    # Act
    result = run(cli, runner, environ, "pr", "comment", "create", "7", *REPO, "-m", "plain")
    # Assert
    assert result.exit_code == ExitCode.OK
    assert body_of(route.calls.last.request) == {"content": {"raw": "plain"}}


@respx.mock
def test_commit_prs_lists_the_pull_requests_of_a_commit(
    cli: Typer, runner: CliRunner, environ: dict[str, str]
) -> None:
    # Arrange
    respx.get(f"{REPOS}/widgets/commit/abc123/pullrequests").mock(return_value=page([PR]))
    # Act
    result = run(cli, runner, environ, "commit", "prs", "abc123", *REPO)
    # Assert
    assert json.loads(result.stdout)[0]["id"] == 7

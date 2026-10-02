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
    from pathlib import Path

    from typer import Typer
    from typer.testing import CliRunner

BASE: Final = f"{REPOS}/widgets"
REPO: Final = ["--repo", "widgets"]
BRANCH: Final[dict[str, object]] = {"type": "branch", "name": "feature", "target": {"hash": "abc"}}
TAG: Final[dict[str, object]] = {"type": "tag", "name": "v1", "target": {"hash": "abc"}, "message": "m"}
COMMIT: Final[dict[str, object]] = {"hash": "abc", "message": "msg", "author": {"raw": "A <a@x>"}}
ACCOUNT: Final[dict[str, object]] = {"display_name": "Some One", "account_id": "a"}
COMMENT: Final[dict[str, object]] = {"id": 3, "content": {"raw": "hi"}}
STATUS: Final[dict[str, object]] = {"key": "ci", "state": "SUCCESSFUL", "url": "https://ci.test"}
REPORT: Final[dict[str, object]] = {"external_id": "r1", "title": "Scan", "result": "PASSED", "report_type": "BUG"}
ANNOTATION: Final[dict[str, object]] = {"external_id": "a1", "title": "Bad", "path": "a.py", "line": 3}


@respx.mock
def test_branch_and_tag_crud(cli: Typer, runner: CliRunner, environ: dict[str, str]) -> None:
    # Arrange
    respx.get(f"{BASE}/refs/branches").mock(return_value=page([BRANCH]))
    respx.get(f"{BASE}/refs/branches/feature").mock(return_value=httpx.Response(200, json=BRANCH))
    branch_created = respx.post(f"{BASE}/refs/branches").mock(return_value=httpx.Response(201, json=BRANCH))
    branch_deleted = respx.delete(f"{BASE}/refs/branches/feature").mock(return_value=httpx.Response(204))
    respx.get(f"{BASE}/refs/tags").mock(return_value=page([TAG]))
    respx.get(f"{BASE}/refs/tags/v1").mock(return_value=httpx.Response(200, json=TAG))
    tag_created = respx.post(f"{BASE}/refs/tags").mock(return_value=httpx.Response(201, json=TAG))
    tag_deleted = respx.delete(f"{BASE}/refs/tags/v1").mock(return_value=httpx.Response(204))
    respx.get(f"{BASE}/refs").mock(return_value=page([BRANCH, TAG]))
    # Act
    branches = run(cli, runner, environ, "branch", "list", *REPO)
    branch = run(cli, runner, environ, "branch", "get", "feature", *REPO)
    branch_create = run(cli, runner, environ, "branch", "create", "feature", *REPO, "--target", "abc")
    branch_delete = run(cli, runner, environ, "branch", "delete", "feature", *REPO, "--yes")
    tags = run(cli, runner, environ, "tag", "list", *REPO)
    tag = run(cli, runner, environ, "tag", "get", "v1", *REPO)
    tag_create = run(cli, runner, environ, "tag", "create", "v1", *REPO, "--target", "abc", "-m", "m")
    tag_delete = run(cli, runner, environ, "tag", "delete", "v1", *REPO, "--yes")
    refs = run(cli, runner, environ, "ref", "list", *REPO)
    # Assert
    assert json.loads(branches.stdout)[0]["name"] == "feature"
    assert json.loads(branch.stdout)["name"] == "feature"
    assert json.loads(tags.stdout)[0]["name"] == "v1"
    assert json.loads(tag.stdout)["name"] == "v1"
    assert len(json.loads(refs.stdout)) == 2
    assert body_of(branch_created.calls.last.request) == {"name": "feature", "target": {"hash": "abc"}}
    assert body_of(tag_created.calls.last.request) == {"name": "v1", "target": {"hash": "abc"}, "message": "m"}
    assert branch_create.exit_code == tag_create.exit_code == ExitCode.OK
    assert branch_delete.exit_code == tag_delete.exit_code == ExitCode.OK
    assert branch_deleted.called
    assert tag_deleted.called


@respx.mock
def test_commit_list_uses_get_for_one_filter_and_post_for_several(
    cli: Typer, runner: CliRunner, environ: dict[str, str]
) -> None:
    # Arrange
    plain = respx.get(f"{BASE}/commits").mock(return_value=page([COMMIT]))
    from_revision = respx.get(f"{BASE}/commits/main").mock(return_value=page([COMMIT]))
    posted = respx.post(f"{BASE}/commits").mock(return_value=page([COMMIT]))
    posted_from = respx.post(f"{BASE}/commits/main").mock(return_value=page([COMMIT]))
    # Act
    one = run(cli, runner, environ, "commit", "list", *REPO, "--include", "dev", "--exclude", "main")
    revision = run(cli, runner, environ, "commit", "list", *REPO, "--revision", "main")
    many = run(cli, runner, environ, "commit", "list", *REPO, "--include", "a", "--include", "b")
    forced = run(cli, runner, environ, "commit", "list", *REPO, "--revision", "main", "--post")
    # Assert
    assert json.loads(one.stdout)[0]["hash"] == "abc"
    assert revision.exit_code == ExitCode.OK
    assert plain.calls.last.request.url.params["include"] == "dev"
    assert plain.calls.last.request.url.params["exclude"] == "main"
    assert from_revision.called
    assert many.exit_code == ExitCode.OK
    assert b"include=a" in posted.calls.last.request.content
    assert forced.exit_code == ExitCode.OK
    assert posted_from.called


@respx.mock
def test_commit_read_commands(cli: Typer, runner: CliRunner, environ: dict[str, str]) -> None:
    # Arrange
    respx.get(f"{BASE}/commit/abc").mock(return_value=httpx.Response(200, json=COMMIT))
    respx.get(f"{BASE}/merge-base/a..b").mock(return_value=httpx.Response(200, json=COMMIT))
    respx.post(f"{BASE}/commit/abc/approve").mock(return_value=httpx.Response(200, json=ACCOUNT))
    respx.delete(f"{BASE}/commit/abc/approve").mock(return_value=httpx.Response(204))
    respx.get(f"{BASE}/diff/abc").mock(return_value=httpx.Response(200, text="diff"))
    respx.get(f"{BASE}/patch/abc").mock(return_value=httpx.Response(200, text="patch"))
    respx.get(f"{BASE}/diffstat/abc").mock(return_value=page([{"status": "added", "new": {"path": "a"}}]))
    respx.get(f"{BASE}/file-conflicts/a..b").mock(return_value=page([{"path": "a", "scenario": "content"}]))
    # Act
    got = run(cli, runner, environ, "commit", "get", "abc", *REPO)
    base = run(cli, runner, environ, "commit", "merge-base", "a..b", *REPO)
    approve = run(cli, runner, environ, "commit", "approve", "abc", *REPO)
    unapprove = run(cli, runner, environ, "commit", "unapprove", "abc", *REPO)
    diff = run(cli, runner, environ, "commit", "diff", "abc", *REPO)
    text = run(cli, runner, environ, "commit", "patch", "abc", *REPO)
    stat = run(cli, runner, environ, "commit", "diffstat", "abc", *REPO)
    conflicts = run(cli, runner, environ, "commit", "conflicts", "a..b", *REPO)
    # Assert
    assert json.loads(got.stdout)["hash"] == "abc"
    assert json.loads(base.stdout)["hash"] == "abc"
    assert approve.exit_code == unapprove.exit_code == ExitCode.OK
    assert diff.stdout == "diff\n"
    assert text.stdout == "patch\n"
    assert json.loads(stat.stdout)[0]["status"] == "added"
    assert json.loads(conflicts.stdout)[0]["scenario"] == "content"


@respx.mock
def test_commit_comment_commands(cli: Typer, runner: CliRunner, environ: dict[str, str]) -> None:
    # Arrange
    comments = f"{BASE}/commit/abc/comments"
    respx.get(comments).mock(return_value=page([COMMENT]))
    respx.get(f"{comments}/3").mock(return_value=httpx.Response(200, json=COMMENT))
    created = respx.post(comments).mock(return_value=httpx.Response(201, json=COMMENT))
    updated = respx.put(f"{comments}/3").mock(return_value=httpx.Response(200, json=COMMENT))
    deleted = respx.delete(f"{comments}/3").mock(return_value=httpx.Response(204))
    # Act
    listed = run(cli, runner, environ, "commit", "comment", "list", "abc", *REPO)
    got = run(cli, runner, environ, "commit", "comment", "get", "abc", "3", *REPO)
    create = run(cli, runner, environ, "commit", "comment", "create", "abc", *REPO, "-m", "hi", "--inline-path", "a")
    plain = run(cli, runner, environ, "commit", "comment", "create", "abc", *REPO, "-m", "plain")
    update = run(cli, runner, environ, "commit", "comment", "update", "abc", "3", *REPO, "-m", "bye")
    delete = run(cli, runner, environ, "commit", "comment", "delete", "abc", "3", *REPO, "--yes")
    # Assert
    assert json.loads(listed.stdout)[0]["id"] == 3
    assert json.loads(got.stdout)["id"] == 3
    assert body_of(created.calls[0].request) == {"content": {"raw": "hi"}, "inline": {"path": "a"}}
    assert body_of(created.calls[1].request) == {"content": {"raw": "plain"}}
    assert body_of(updated.calls.last.request) == {"content": {"raw": "bye"}}
    assert create.exit_code == plain.exit_code == update.exit_code == delete.exit_code == ExitCode.OK
    assert deleted.called


@respx.mock
def test_commit_status_commands(cli: Typer, runner: CliRunner, environ: dict[str, str]) -> None:
    # Arrange
    statuses = f"{BASE}/commit/abc/statuses"
    respx.get(statuses).mock(return_value=page([STATUS]))
    respx.get(f"{statuses}/build/ci").mock(return_value=httpx.Response(200, json=STATUS))
    created = respx.post(f"{statuses}/build").mock(return_value=httpx.Response(201, json=STATUS))
    updated = respx.put(f"{statuses}/build/ci").mock(return_value=httpx.Response(200, json=STATUS))
    # Act
    listed = run(cli, runner, environ, "commit", "status", "list", "abc", *REPO)
    got = run(cli, runner, environ, "commit", "status", "get", "abc", "ci", *REPO)
    create = run(
        cli,
        runner,
        environ,
        *["commit", "status", "create", "abc", *REPO, "--key", "ci", "--state", "SUCCESSFUL"],
        *["--url", "https://ci.test", "--name", "CI", "--description", "ok"],
    )
    update = run(cli, runner, environ, "commit", "status", "update", "abc", "ci", *REPO, "--state", "FAILED")
    # Assert
    assert json.loads(listed.stdout)[0]["key"] == "ci"
    assert json.loads(got.stdout)["key"] == "ci"
    assert body_of(created.calls.last.request) == {
        "key": "ci",
        "state": "SUCCESSFUL",
        "url": "https://ci.test",
        "name": "CI",
        "description": "ok",
    }
    assert body_of(updated.calls.last.request) == {"state": "FAILED"}
    assert create.exit_code == update.exit_code == ExitCode.OK


@respx.mock
def test_commit_property_commands(cli: Typer, runner: CliRunner, environ: dict[str, str]) -> None:
    # Arrange
    prop = f"{BASE}/commit/abc/properties/app/flag"
    respx.get(prop).mock(return_value=httpx.Response(200, json=[1]))
    stored = respx.put(prop).mock(return_value=httpx.Response(204))
    deleted = respx.delete(prop).mock(return_value=httpx.Response(204))
    # Act
    got = run(cli, runner, environ, "commit", "property", "get", "abc", "app", "flag", *REPO)
    set_value = run(cli, runner, environ, "commit", "property", "set", "abc", "app", "flag", "[2]", *REPO)
    delete = run(cli, runner, environ, "commit", "property", "delete", "abc", "app", "flag", *REPO)
    # Assert
    assert json.loads(got.stdout) == [1]
    assert json.loads(stored.calls.last.request.content) == [2]
    assert set_value.exit_code == delete.exit_code == ExitCode.OK
    assert deleted.called


@respx.mock
def test_source_ls_lists_the_root_a_path_and_requires_a_rev_for_a_path(
    cli: Typer, runner: CliRunner, environ: dict[str, str]
) -> None:
    # Arrange
    entry = {"type": "commit_file", "path": "a.py", "size": 3, "commit": {"hash": "abc"}}
    respx.get(f"{BASE}/src").mock(return_value=page([entry]))
    respx.get(f"{BASE}/src/main/docs").mock(return_value=page([entry]))
    bare_route = respx.get(f"{BASE}/src/main/").mock(return_value=page([entry]))
    # Act
    root = run(cli, runner, environ, "source", "ls", *REPO)
    path = run(cli, runner, environ, "source", "ls", "docs", *REPO, "--rev", "main")
    bare = run(cli, runner, environ, "source", "ls", *REPO, "--rev", "main")
    refused = run(cli, runner, environ, "source", "ls", "docs", *REPO)
    # Assert
    assert json.loads(root.stdout)[0]["path"] == "a.py"
    assert json.loads(path.stdout)[0]["path"] == "a.py"
    assert bare.exit_code == ExitCode.OK
    assert bare_route.called
    assert refused.exit_code == ExitCode.USAGE


@respx.mock
def test_source_cat_streams_bytes_or_saves_a_file(
    cli: Typer, runner: CliRunner, environ: dict[str, str], tmp_path: Path
) -> None:
    # Arrange
    respx.get(f"{BASE}/src/main/a.bin").mock(return_value=httpx.Response(200, content=b"\x00\x01data"))
    target = tmp_path / "out.bin"
    # Act
    streamed = run(cli, runner, environ, "source", "cat", "main", "a.bin", *REPO)
    saved = run(cli, runner, environ, "source", "cat", "main", "a.bin", *REPO, "--output-file", str(target))
    # Assert
    assert streamed.stdout_bytes == b"\x00\x01data"
    assert saved.exit_code == ExitCode.OK
    assert target.read_bytes() == b"\x00\x01data"


@respx.mock
def test_source_history_and_commit(cli: Typer, runner: CliRunner, environ: dict[str, str], tmp_path: Path) -> None:
    # Arrange
    respx.get(f"{BASE}/filehistory/main/a.py").mock(return_value=page([{"path": "a.py", "commit": {"hash": "abc"}}]))
    committed = respx.post(f"{BASE}/src").mock(return_value=httpx.Response(201))
    local = tmp_path / "local.txt"
    local.write_text("hello")
    # Act
    history = run(cli, runner, environ, "source", "history", "main", "a.py", *REPO)
    commit = run(
        cli,
        runner,
        environ,
        *["source", "commit", *REPO, "--file", f"{local}:docs/remote.txt", "-m", "add", "--branch", "main"],
        *["--author", "A <a@x>"],
    )
    missing = run(cli, runner, environ, "source", "commit", *REPO, "--file", str(tmp_path / "nope"))
    # Assert
    assert json.loads(history.stdout)[0]["commit"]["hash"] == "abc"
    assert commit.exit_code == ExitCode.OK
    assert b'filename="docs/remote.txt"' in committed.calls.last.request.content
    assert missing.exit_code == ExitCode.USAGE


@respx.mock
def test_download_commands(cli: Typer, runner: CliRunner, environ: dict[str, str], tmp_path: Path) -> None:
    # Arrange
    respx.get(f"{BASE}/downloads").mock(return_value=page([{"name": "a.zip", "size": 3, "downloads": 1}]))
    respx.get(f"{BASE}/downloads/a.zip").mock(return_value=httpx.Response(200, content=b"zip"))
    uploaded = respx.post(f"{BASE}/downloads").mock(return_value=httpx.Response(201))
    deleted = respx.delete(f"{BASE}/downloads/a.zip").mock(return_value=httpx.Response(204))
    source = tmp_path / "b.zip"
    source.write_bytes(b"zzz")
    target = tmp_path / "saved.zip"
    # Act
    listed = run(cli, runner, environ, "download", "list", *REPO)
    streamed = run(cli, runner, environ, "download", "get", "a.zip", *REPO)
    saved = run(cli, runner, environ, "download", "get", "a.zip", *REPO, "--output-file", str(target))
    upload = run(cli, runner, environ, "download", "upload", str(source), *REPO, "--name", "c.zip")
    missing = run(cli, runner, environ, "download", "upload", str(tmp_path / "nope"), *REPO)
    delete = run(cli, runner, environ, "download", "delete", "a.zip", *REPO, "--yes")
    # Assert
    assert json.loads(listed.stdout)[0]["name"] == "a.zip"
    assert streamed.stdout_bytes == b"zip"
    assert target.read_bytes() == b"zip"
    assert saved.exit_code == upload.exit_code == delete.exit_code == ExitCode.OK
    assert b'filename="c.zip"' in uploaded.calls.last.request.content
    assert missing.exit_code == ExitCode.USAGE
    assert deleted.called


@respx.mock
def test_report_commands(cli: Typer, runner: CliRunner, environ: dict[str, str]) -> None:
    # Arrange
    reports = f"{BASE}/commit/abc/reports"
    respx.get(reports).mock(return_value=page([REPORT]))
    respx.get(f"{reports}/r1").mock(return_value=httpx.Response(200, json=REPORT))
    put_route = respx.put(f"{reports}/r1").mock(return_value=httpx.Response(200, json=REPORT))
    deleted = respx.delete(f"{reports}/r1").mock(return_value=httpx.Response(204))
    # Act
    listed = run(cli, runner, environ, "report", "list", "abc", *REPO)
    got = run(cli, runner, environ, "report", "get", "abc", "r1", *REPO)
    put = run(
        cli,
        runner,
        environ,
        *["report", "put", "abc", "r1", *REPO, "--title", "Scan", "--details", "d", "--reporter", "tool"],
        *["--link", "https://x.test", "--type", "BUG", "--result", "PASSED"],
    )
    delete = run(cli, runner, environ, "report", "delete", "abc", "r1", *REPO, "--yes")
    # Assert
    assert json.loads(listed.stdout)[0]["external_id"] == "r1"
    assert json.loads(got.stdout)["title"] == "Scan"
    assert body_of(put_route.calls.last.request) == {
        "title": "Scan",
        "details": "d",
        "reporter": "tool",
        "link": "https://x.test",
        "report_type": "BUG",
        "result": "PASSED",
    }
    assert put.exit_code == delete.exit_code == ExitCode.OK
    assert deleted.called


@respx.mock
def test_annotation_commands(cli: Typer, runner: CliRunner, environ: dict[str, str]) -> None:
    # Arrange
    notes = f"{BASE}/commit/abc/reports/r1/annotations"
    respx.get(notes).mock(return_value=page([ANNOTATION]))
    respx.get(f"{notes}/a1").mock(return_value=httpx.Response(200, json=ANNOTATION))
    put_route = respx.put(f"{notes}/a1").mock(return_value=httpx.Response(200, json=ANNOTATION))
    bulk = respx.post(notes).mock(return_value=httpx.Response(200, json=[ANNOTATION]))
    deleted = respx.delete(f"{notes}/a1").mock(return_value=httpx.Response(204))
    # Act
    listed = run(cli, runner, environ, "annotation", "list", "abc", "r1", *REPO)
    got = run(cli, runner, environ, "annotation", "get", "abc", "r1", "a1", *REPO)
    put = run(
        cli,
        runner,
        environ,
        *["annotation", "put", "abc", "r1", "a1", *REPO, "--title", "Bad", "--summary", "s", "--details", "d"],
        *["--path", "a.py", "--line", "3", "--type", "BUG", "--result", "FAILED", "--severity", "HIGH", "--link", "l"],
    )
    many_put = run(
        cli,
        runner,
        environ,
        *["annotation", "put-many", "abc", "r1", *REPO, "--from-file", "-"],
        stdin='[{"external_id": "a1", "title": "Bad"}]',
    )
    delete = run(cli, runner, environ, "annotation", "delete", "abc", "r1", "a1", *REPO, "--yes")
    # Assert
    assert json.loads(listed.stdout)[0]["external_id"] == "a1"
    assert json.loads(got.stdout)["line"] == 3
    assert body_of(put_route.calls.last.request)["severity"] == "HIGH"
    assert put.exit_code == many_put.exit_code == delete.exit_code == ExitCode.OK
    assert json.loads(bulk.calls.last.request.content) == [{"external_id": "a1", "title": "Bad"}]
    assert deleted.called


def test_annotation_put_many_rejects_a_body_that_is_not_an_array(
    cli: Typer, runner: CliRunner, environ: dict[str, str]
) -> None:
    # Arrange
    arguments = ["annotation", "put-many", "abc", "r1", *REPO, "--from-file", "-"]
    # Act
    result = run(cli, runner, environ, *arguments, stdin="{}")
    # Assert
    assert result.exit_code == ExitCode.USAGE


def test_annotation_put_many_rejects_an_invalid_item(cli: Typer, runner: CliRunner, environ: dict[str, str]) -> None:
    # Arrange
    arguments = ["annotation", "put-many", "abc", "r1", *REPO, "--from-file", "-"]
    # Act
    result = run(cli, runner, environ, *arguments, stdin='[{"line": "x"}]')
    # Assert
    assert result.exit_code == ExitCode.USAGE

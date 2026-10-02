from __future__ import annotations

import json
from typing import TYPE_CHECKING
from typing import Final

import httpx
import respx

from bitbucket_unofficial_cli.runtime.exit_codes import ExitCode
from tests.conftest import BASE_URL
from tests.unit.commands.support import body_of
from tests.unit.commands.support import page
from tests.unit.commands.support import run

if TYPE_CHECKING:
    from pathlib import Path

    from typer import Typer
    from typer.testing import CliRunner

SNIPPETS: Final = f"{BASE_URL}/snippets/acme"
ONE: Final = f"{SNIPPETS}/abc"
SNIPPET: Final[dict[str, object]] = {
    "id": "abc",
    "title": "Hello",
    "is_private": True,
    "owner": {"display_name": "Me"},
}
COMMIT: Final[dict[str, object]] = {"hash": "r1", "message": "m", "author": {"raw": "A <a@x>"}}
COMMENT: Final[dict[str, object]] = {"id": 3, "content": {"raw": "hi"}}


@respx.mock
def test_snippet_list_get_and_delete(cli: Typer, runner: CliRunner, environ: dict[str, str]) -> None:
    # Arrange
    listing = respx.get(SNIPPETS).mock(return_value=page([SNIPPET]))
    respx.get(ONE).mock(return_value=httpx.Response(200, json=SNIPPET))
    deleted = respx.delete(ONE).mock(return_value=httpx.Response(204))
    # Act
    listed = run(cli, runner, environ, "snippet", "list", "--role", "owner")
    plain = run(cli, runner, environ, "snippet", "list")
    got = run(cli, runner, environ, "snippet", "get", "abc")
    refused = run(cli, runner, environ, "snippet", "list", "--role", "bogus")
    delete = run(cli, runner, environ, "snippet", "delete", "abc", "--yes")
    # Assert
    assert json.loads(listed.stdout)[0]["id"] == "abc"
    assert dict(listing.calls[0].request.url.params) == {"role": "owner"}
    assert plain.exit_code == ExitCode.OK
    assert json.loads(got.stdout)["title"] == "Hello"
    assert refused.exit_code == ExitCode.USAGE
    assert delete.exit_code == ExitCode.OK
    assert deleted.called


@respx.mock
def test_snippet_create_uploads_the_files_in_the_workspace_or_personally(
    cli: Typer, runner: CliRunner, environ: dict[str, str], tmp_path: Path
) -> None:
    # Arrange
    workspace = respx.post(SNIPPETS).mock(return_value=httpx.Response(201, json=SNIPPET))
    personal = respx.post(f"{BASE_URL}/snippets").mock(return_value=httpx.Response(201, json=SNIPPET))
    local = tmp_path / "a.txt"
    local.write_text("hello")
    # Act
    created = run(
        cli, runner, environ, "snippet", "create", "--title", "Hello", "--private", "--file", f"{local}:docs/a.txt"
    )
    own = run(cli, runner, environ, "snippet", "create", "--personal", "--file", str(local))
    missing = run(cli, runner, environ, "snippet", "create", "--file", str(tmp_path / "nope"))
    # Assert
    assert created.exit_code == own.exit_code == ExitCode.OK
    assert b'name="title"' in workspace.calls.last.request.content
    assert b'filename="docs/a.txt"' in workspace.calls.last.request.content
    assert personal.called
    assert missing.exit_code == ExitCode.USAGE


@respx.mock
def test_snippet_update_sends_json_for_metadata_and_multipart_for_files(
    cli: Typer, runner: CliRunner, environ: dict[str, str], tmp_path: Path
) -> None:
    # Arrange
    route = respx.put(ONE).mock(return_value=httpx.Response(200, json=SNIPPET))
    local = tmp_path / "b.txt"
    local.write_text("x")
    # Act
    metadata = run(cli, runner, environ, "snippet", "update", "abc", "--title", "New", "--public")
    files = run(cli, runner, environ, "snippet", "update", "abc", "--file", str(local), "--delete-file", "old.txt")
    # Assert
    assert metadata.exit_code == files.exit_code == ExitCode.OK
    assert body_of(route.calls[0].request) == {"title": "New", "is_private": False}
    assert b'name="files"' in route.calls[1].request.content
    assert b"old.txt" in route.calls[1].request.content


@respx.mock
def test_snippet_file_prints_or_saves_the_latest_or_a_revision(
    cli: Typer, runner: CliRunner, environ: dict[str, str], tmp_path: Path
) -> None:
    # Arrange
    respx.get(f"{ONE}/files/a.txt").mock(return_value=httpx.Response(200, content=b"latest"))
    respx.get(f"{ONE}/r1/files/a.txt").mock(return_value=httpx.Response(200, content=b"old"))
    target = tmp_path / "out.txt"
    # Act
    latest = run(cli, runner, environ, "snippet", "file", "abc", "a.txt")
    old = run(cli, runner, environ, "snippet", "file", "abc", "a.txt", "--revision", "r1")
    saved = run(cli, runner, environ, "snippet", "file", "abc", "a.txt", "--output-file", str(target))
    # Assert
    assert latest.stdout_bytes == b"latest"
    assert old.stdout_bytes == b"old"
    assert saved.exit_code == ExitCode.OK
    assert target.read_bytes() == b"latest"


@respx.mock
def test_snippet_history_and_revision_text(cli: Typer, runner: CliRunner, environ: dict[str, str]) -> None:
    # Arrange
    respx.get(f"{ONE}/commits").mock(return_value=page([COMMIT]))
    respx.get(f"{ONE}/commits/r1").mock(return_value=httpx.Response(200, json=COMMIT))
    diff = respx.get(f"{ONE}/r1/diff").mock(return_value=httpx.Response(200, text="diff"))
    respx.get(f"{ONE}/r1/patch").mock(return_value=httpx.Response(200, text="patch"))
    # Act
    commits = run(cli, runner, environ, "snippet", "commits", "abc")
    commit = run(cli, runner, environ, "snippet", "commit", "abc", "r1")
    shown = run(cli, runner, environ, "snippet", "diff", "abc", "r1", "--path", "a.txt")
    patch = run(cli, runner, environ, "snippet", "patch", "abc", "r1")
    # Assert
    assert json.loads(commits.stdout)[0]["hash"] == "r1"
    assert json.loads(commit.stdout)["hash"] == "r1"
    assert shown.stdout == "diff\n"
    assert dict(diff.calls.last.request.url.params) == {"path": "a.txt"}
    assert patch.stdout == "patch\n"


@respx.mock
def test_snippet_watching_commands(cli: Typer, runner: CliRunner, environ: dict[str, str]) -> None:
    # Arrange
    watch = f"{ONE}/watch"
    put = respx.put(watch).mock(return_value=httpx.Response(204))
    deleted = respx.delete(watch).mock(return_value=httpx.Response(204))
    check = respx.get(watch).mock(side_effect=[httpx.Response(204), httpx.Response(404, json={"type": "error"})])
    respx.get(f"{ONE}/watchers").mock(return_value=page([{"display_name": "Me", "account_id": "a"}]))
    # Act
    start = run(cli, runner, environ, "snippet", "watch", "abc")
    stop = run(cli, runner, environ, "snippet", "unwatch", "abc")
    yes = run(cli, runner, environ, "snippet", "is-watching", "abc")
    no = run(cli, runner, environ, "snippet", "is-watching", "abc")
    watchers = run(cli, runner, environ, "snippet", "watchers", "abc")
    # Assert
    assert start.exit_code == stop.exit_code == ExitCode.OK
    assert put.called
    assert deleted.called
    assert json.loads(yes.stdout) == {"watching": True}
    assert json.loads(no.stdout) == {"watching": False}
    assert check.call_count == 2
    assert json.loads(watchers.stdout)[0]["account_id"] == "a"


@respx.mock
def test_snippet_comment_commands(cli: Typer, runner: CliRunner, environ: dict[str, str]) -> None:
    # Arrange
    base = f"{ONE}/comments"
    respx.get(base).mock(return_value=page([COMMENT]))
    respx.get(f"{base}/3").mock(return_value=httpx.Response(200, json=COMMENT))
    created = respx.post(base).mock(return_value=httpx.Response(201, json=COMMENT))
    updated = respx.put(f"{base}/3").mock(return_value=httpx.Response(200, json=COMMENT))
    deleted = respx.delete(f"{base}/3").mock(return_value=httpx.Response(204))
    # Act
    listed = run(cli, runner, environ, "snippet", "comment", "list", "abc")
    got = run(cli, runner, environ, "snippet", "comment", "get", "abc", "3")
    create = run(cli, runner, environ, "snippet", "comment", "create", "abc", "-m", "hi", "--parent", "2")
    update = run(cli, runner, environ, "snippet", "comment", "update", "abc", "3", "-m", "bye")
    delete = run(cli, runner, environ, "snippet", "comment", "delete", "abc", "3", "--yes")
    # Assert
    assert json.loads(listed.stdout)[0]["id"] == 3
    assert json.loads(got.stdout)["id"] == 3
    assert body_of(created.calls.last.request) == {"content": {"raw": "hi"}, "parent": {"id": 2}}
    assert body_of(updated.calls.last.request) == {"content": {"raw": "bye"}}
    assert create.exit_code == update.exit_code == delete.exit_code == ExitCode.OK
    assert deleted.called


@respx.mock
def test_snippet_revision_commands(cli: Typer, runner: CliRunner, environ: dict[str, str], tmp_path: Path) -> None:
    # Arrange
    url = f"{ONE}/r1"
    respx.get(url).mock(return_value=httpx.Response(200, json=SNIPPET))
    updated = respx.put(url).mock(return_value=httpx.Response(200, json=SNIPPET))
    deleted = respx.delete(url).mock(return_value=httpx.Response(204))
    local = tmp_path / "c.txt"
    local.write_text("x")
    # Act
    got = run(cli, runner, environ, "snippet", "revision", "get", "abc", "r1")
    update = run(cli, runner, environ, "snippet", "revision", "update", "abc", "r1", "--title", "T", "--private")
    upload = run(cli, runner, environ, "snippet", "revision", "update", "abc", "r1", "--file", str(local))
    delete = run(cli, runner, environ, "snippet", "revision", "delete", "abc", "r1", "--yes")
    # Assert
    assert json.loads(got.stdout)["id"] == "abc"
    assert body_of(updated.calls[0].request) == {"title": "T", "is_private": True}
    assert update.exit_code == upload.exit_code == delete.exit_code == ExitCode.OK
    assert deleted.called

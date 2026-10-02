from dataclasses import dataclass
from pathlib import Path
from typing import Annotated
from typing import Final

import typer
from bitbucket.models.snippet import SnippetCreate
from bitbucket.models.snippet import SnippetRole
from bitbucket.models.snippet import SnippetUpdate

from bitbucket_unofficial_cli.commands import snippet_comment
from bitbucket_unofficial_cli.commands import snippet_revision
from bitbucket_unofficial_cli.output.columns import ACCOUNTS
from bitbucket_unofficial_cli.output.columns import COMMITS
from bitbucket_unofficial_cli.output.columns import SNIPPET
from bitbucket_unofficial_cli.output.columns import SNIPPETS
from bitbucket_unofficial_cli.output.renderer import Column
from bitbucket_unofficial_cli.output.renderer import many
from bitbucket_unofficial_cli.output.renderer import single
from bitbucket_unofficial_cli.runtime.context import get_app_context
from bitbucket_unofficial_cli.runtime.errors import handle_errors
from bitbucket_unofficial_cli.runtime.params import PagingOptions
from bitbucket_unofficial_cli.runtime.params import Yes
from bitbucket_unofficial_cli.runtime.params import one_of
from bitbucket_unofficial_cli.runtime.params import options_from
from bitbucket_unofficial_cli.services.files import read_local_files
from bitbucket_unofficial_cli.services.listing import paged
from bitbucket_unofficial_cli.services.payloads import build
from bitbucket_unofficial_cli.services.payloads import check_choice

APP: Final = typer.Typer(help="Manage the snippets of the selected workspace.", no_args_is_help=True)
APP.add_typer(snippet_comment.APP, name="comment")
APP.add_typer(snippet_revision.APP, name="revision")

SnippetId = Annotated[str, typer.Argument(help="Snippet ID.")]  # pylint: disable=gajaguar-module-const-naming,gajaguar-require-final
Revision = Annotated[str, typer.Argument(help="Revision hash.")]  # pylint: disable=gajaguar-module-const-naming,gajaguar-require-final
_WATCHING: Final = (Column("watching", "Watching"),)


@dataclass(frozen=True, slots=True, kw_only=True)
class _ListOptions(PagingOptions):
    role: Annotated[
        str | None, typer.Option("--role", help="Only snippets you have this role in. " + one_of(SnippetRole))
    ] = None


@dataclass(frozen=True, slots=True, kw_only=True)
class _CreateOptions:
    title: Annotated[str | None, typer.Option("--title", help="Snippet title.")] = None
    private: Annotated[bool | None, typer.Option("--private/--public", help="Snippet visibility.")] = None
    files: Annotated[
        list[str] | None,
        typer.Option("--file", help="LOCAL or LOCAL:REMOTE file to add; repeatable."),
    ] = None
    personal: Annotated[bool, typer.Option("--personal", help="Create it under your account, not the workspace.")] = (
        False
    )


@dataclass(frozen=True, slots=True, kw_only=True)
class _UpdateOptions:
    snippet_id: SnippetId
    title: Annotated[str | None, typer.Option("--title", help="New title.")] = None
    private: Annotated[bool | None, typer.Option("--private/--public", help="Snippet visibility.")] = None
    files: Annotated[
        list[str] | None, typer.Option("--file", help="LOCAL or LOCAL:REMOTE file to add or replace.")
    ] = None
    delete_files: Annotated[list[str] | None, typer.Option("--delete-file", help="Path to remove; repeatable.")] = None


@dataclass(frozen=True, slots=True, kw_only=True)
class _FileOptions:
    snippet_id: SnippetId
    path: Annotated[str, typer.Argument(help="Path of the file in the snippet.")]
    revision: Annotated[str | None, typer.Option("--revision", help="Revision hash; defaults to the latest.")] = None
    output_file: Annotated[Path | None, typer.Option("--output-file", help="Write the file here.")] = None


@dataclass(frozen=True, slots=True, kw_only=True)
class _DiffOptions:
    snippet_id: SnippetId
    revision: Revision
    path: Annotated[str | None, typer.Option("--path", help="Only this file.")] = None


@dataclass(frozen=True, slots=True, kw_only=True)
class _PagedSnippet(PagingOptions):
    snippet_id: SnippetId


@APP.command(name="list", help="List the snippets of the workspace.")
@handle_errors
@options_from(_ListOptions)
def list_snippets(ctx: typer.Context, options: _ListOptions) -> None:
    app_context = get_app_context(ctx)
    snippets = app_context.workspace().snippets
    checked = check_choice(options.role, SnippetRole, "--role")
    role = SnippetRole(checked) if checked else None
    found = paged(
        app_context,
        options,
        lambda: snippets.list(role=role),
        lambda **page: snippets.list_page(role=role, **page),
    )
    app_context.render(many(found, SNIPPETS, id_key="id"))


@APP.command(help="Show a snippet.")
@handle_errors
def get(ctx: typer.Context, snippet_id: SnippetId) -> None:
    app_context = get_app_context(ctx)
    app_context.render(single(app_context.workspace().snippets.get(snippet_id), SNIPPET, id_key="id"))


@APP.command(help="Create a snippet from local files.")
@handle_errors
@options_from(_CreateOptions)
def create(ctx: typer.Context, options: _CreateOptions) -> None:
    app_context = get_app_context(ctx)
    payload = build(SnippetCreate, title=options.title, is_private=options.private)
    files = read_local_files(options.files or [])
    snippets = app_context.client().snippets if options.personal else app_context.workspace().snippets
    app_context.render(single(snippets.create(payload, files=files), SNIPPET, id_key="id"))


@APP.command(help="Change a snippet's title, visibility or files.")
@handle_errors
@options_from(_UpdateOptions)
def update(ctx: typer.Context, options: _UpdateOptions) -> None:
    app_context = get_app_context(ctx)
    payload = build(SnippetUpdate, title=options.title, is_private=options.private)
    updated = app_context.workspace().snippets.update(
        options.snippet_id,
        payload,
        files=read_local_files(options.files or []),
        delete_files=options.delete_files or [],
    )
    app_context.render(single(updated, SNIPPET, id_key="id"))


@APP.command(help="Delete a snippet.")
@handle_errors
def delete(ctx: typer.Context, snippet_id: SnippetId, *, yes: Yes = False) -> None:
    app_context = get_app_context(ctx)
    app_context.confirm(f"Delete snippet '{snippet_id}'?", assume_yes=yes)
    app_context.workspace().snippets.delete(snippet_id)
    app_context.notify(f"Deleted snippet '{snippet_id}'.")


@APP.command(help="Print a file of a snippet, or save it with --output-file.")
@handle_errors
@options_from(_FileOptions)
def file(ctx: typer.Context, options: _FileOptions) -> None:
    app_context = get_app_context(ctx)
    snippet = app_context.workspace().snippet(options.snippet_id)
    content = snippet.revision(options.revision).file(options.path) if options.revision else snippet.file(options.path)
    if options.output_file is None:
        app_context.write_bytes(content)
    else:
        options.output_file.write_bytes(content)
        app_context.notify(f"Wrote {len(content)} bytes to {options.output_file}.")


@APP.command(help="List the revisions of a snippet.")
@handle_errors
@options_from(_PagedSnippet)
def commits(ctx: typer.Context, options: _PagedSnippet) -> None:
    app_context = get_app_context(ctx)
    snippet = app_context.workspace().snippet(options.snippet_id)
    found = paged(app_context, options, snippet.commits, snippet.commits_page)
    app_context.render(many(found, COMMITS, id_key="hash"))


@APP.command(help="Show one revision of a snippet.")
@handle_errors
def commit(ctx: typer.Context, snippet_id: SnippetId, revision: Revision) -> None:
    app_context = get_app_context(ctx)
    found = app_context.workspace().snippet(snippet_id).commit(revision)
    app_context.render(single(found, COMMITS, id_key="hash"))


@APP.command(help="Print the diff of a revision.")
@handle_errors
@options_from(_DiffOptions)
def diff(ctx: typer.Context, options: _DiffOptions) -> None:
    app_context = get_app_context(ctx)
    snippet = app_context.workspace().snippet(options.snippet_id)
    app_context.write(snippet.diff(options.revision, path=options.path))


@APP.command(help="Print the patch of a revision.")
@handle_errors
def patch(ctx: typer.Context, snippet_id: SnippetId, revision: Revision) -> None:
    app_context = get_app_context(ctx)
    app_context.write(app_context.workspace().snippet(snippet_id).patch(revision))


@APP.command(help="Watch a snippet.")
@handle_errors
def watch(ctx: typer.Context, snippet_id: SnippetId) -> None:
    app_context = get_app_context(ctx)
    app_context.workspace().snippet(snippet_id).watch()
    app_context.notify(f"Watching snippet '{snippet_id}'.")


@APP.command(help="Stop watching a snippet.")
@handle_errors
def unwatch(ctx: typer.Context, snippet_id: SnippetId) -> None:
    app_context = get_app_context(ctx)
    app_context.workspace().snippet(snippet_id).unwatch()
    app_context.notify(f"No longer watching snippet '{snippet_id}'.")


@APP.command(name="is-watching", help="Say whether you watch a snippet.")
@handle_errors
def is_watching(ctx: typer.Context, snippet_id: SnippetId) -> None:
    app_context = get_app_context(ctx)
    watching = app_context.workspace().snippet(snippet_id).is_watching()
    app_context.render(single({"watching": watching}, _WATCHING, id_key="watching"))


@APP.command(help="List the watchers of a snippet.")
@handle_errors
@options_from(_PagedSnippet)
def watchers(ctx: typer.Context, options: _PagedSnippet) -> None:
    app_context = get_app_context(ctx)
    snippet = app_context.workspace().snippet(options.snippet_id)
    found = paged(app_context, options, snippet.watchers, snippet.watchers_page)
    app_context.render(many(found, ACCOUNTS, id_key="account_id"))

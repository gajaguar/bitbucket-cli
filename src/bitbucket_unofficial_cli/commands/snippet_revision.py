from dataclasses import dataclass
from typing import Annotated
from typing import Final

import typer
from bitbucket.models.snippet import SnippetUpdate

from bitbucket_unofficial_cli.output.columns import SNIPPET
from bitbucket_unofficial_cli.output.renderer import single
from bitbucket_unofficial_cli.runtime.context import get_app_context
from bitbucket_unofficial_cli.runtime.errors import handle_errors
from bitbucket_unofficial_cli.runtime.params import options_from
from bitbucket_unofficial_cli.services.files import read_local_files
from bitbucket_unofficial_cli.services.payloads import build

APP: Final = typer.Typer(
    help="Work with one revision of a snippet; only the latest can be changed.", no_args_is_help=True
)

SnippetId = Annotated[str, typer.Argument(help="Snippet ID.")]  # pylint: disable=gajaguar-module-const-naming,gajaguar-require-final
Node = Annotated[str, typer.Argument(help="Revision hash.")]  # pylint: disable=gajaguar-module-const-naming,gajaguar-require-final


@dataclass(frozen=True, slots=True, kw_only=True)
class _UpdateOptions:
    snippet_id: SnippetId
    node: Node
    title: Annotated[str | None, typer.Option("--title", help="New title.")] = None
    private: Annotated[bool | None, typer.Option("--private/--public", help="Snippet visibility.")] = None
    files: Annotated[
        list[str] | None, typer.Option("--file", help="LOCAL or LOCAL:REMOTE file to add or replace.")
    ] = None
    delete_files: Annotated[list[str] | None, typer.Option("--delete-file", help="Path to remove; repeatable.")] = None


@dataclass(frozen=True, slots=True, kw_only=True)
class _DeleteOptions:
    snippet_id: SnippetId
    node: Node
    yes: Annotated[bool, typer.Option("--yes", "-y", help="Do not ask for confirmation.")] = False


@APP.command(help="Show a snippet as of a revision.")
@handle_errors
def get(ctx: typer.Context, snippet_id: SnippetId, node: Node) -> None:
    app_context = get_app_context(ctx)
    found = app_context.workspace().snippet(snippet_id).revision(node).get()
    app_context.render(single(found, SNIPPET, id_key="id"))


@APP.command(help="Change the latest revision of a snippet.")
@handle_errors
@options_from(_UpdateOptions)
def update(ctx: typer.Context, options: _UpdateOptions) -> None:
    app_context = get_app_context(ctx)
    payload = build(SnippetUpdate, title=options.title, is_private=options.private)
    revision = app_context.workspace().snippet(options.snippet_id).revision(options.node)
    updated = revision.update(
        payload, files=read_local_files(options.files or []), delete_files=options.delete_files or []
    )
    app_context.render(single(updated, SNIPPET, id_key="id"))


@APP.command(help="Delete the latest revision of a snippet.")
@handle_errors
@options_from(_DeleteOptions)
def delete(ctx: typer.Context, options: _DeleteOptions) -> None:
    app_context = get_app_context(ctx)
    app_context.confirm(f"Delete revision '{options.node}'?", assume_yes=options.yes)
    app_context.workspace().snippet(options.snippet_id).revision(options.node).delete()
    app_context.notify(f"Deleted revision '{options.node}'.")

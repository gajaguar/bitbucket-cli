from dataclasses import dataclass
from typing import Annotated
from typing import Final

import typer
from bitbucket.models.comment import CommentUpdate
from bitbucket.models.snippet import SnippetCommentCreate

from bitbucket_unofficial_cli.output.columns import COMMENTS
from bitbucket_unofficial_cli.output.renderer import many
from bitbucket_unofficial_cli.output.renderer import single
from bitbucket_unofficial_cli.runtime.context import get_app_context
from bitbucket_unofficial_cli.runtime.errors import handle_errors
from bitbucket_unofficial_cli.runtime.params import FromFile
from bitbucket_unofficial_cli.runtime.params import PagingOptions
from bitbucket_unofficial_cli.runtime.params import Yes
from bitbucket_unofficial_cli.runtime.params import options_from
from bitbucket_unofficial_cli.services.listing import paged
from bitbucket_unofficial_cli.services.payloads import build

APP: Final = typer.Typer(help="Comment on a snippet.", no_args_is_help=True)

SnippetId = Annotated[str, typer.Argument(help="Snippet ID.")]  # pylint: disable=gajaguar-module-const-naming,gajaguar-require-final
CommentId = Annotated[int, typer.Argument(help="Comment ID.")]  # pylint: disable=gajaguar-module-const-naming,gajaguar-require-final
_Content = Annotated[str | None, typer.Option("--content", "-m", help="Comment text.")]  # pylint: disable=gajaguar-module-const-naming,gajaguar-require-final


@dataclass(frozen=True, slots=True, kw_only=True)
class _ListOptions(PagingOptions):
    snippet_id: SnippetId


@dataclass(frozen=True, slots=True, kw_only=True)
class _CreateOptions:
    snippet_id: SnippetId
    content: _Content = None
    parent: Annotated[int | None, typer.Option("--parent", help="Comment ID to reply to.")] = None
    from_file: FromFile = None


@dataclass(frozen=True, slots=True, kw_only=True)
class _UpdateOptions:
    snippet_id: SnippetId
    comment_id: CommentId
    content: _Content = None
    from_file: FromFile = None


@APP.command(name="list", help="List the comments of a snippet.")
@handle_errors
@options_from(_ListOptions)
def list_comments(ctx: typer.Context, options: _ListOptions) -> None:
    app_context = get_app_context(ctx)
    comments = app_context.workspace().snippet(options.snippet_id).comments
    found = paged(app_context, options, comments.list, comments.list_page)
    app_context.render(many(found, COMMENTS, id_key="id"))


@APP.command(help="Show a comment.")
@handle_errors
def get(ctx: typer.Context, snippet_id: SnippetId, comment_id: CommentId) -> None:
    app_context = get_app_context(ctx)
    comment = app_context.workspace().snippet(snippet_id).comments.get(comment_id)
    app_context.render(single(comment, COMMENTS, id_key="id"))


@APP.command(help="Add a comment, optionally as a reply.")
@handle_errors
@options_from(_CreateOptions)
def create(ctx: typer.Context, options: _CreateOptions) -> None:
    app_context = get_app_context(ctx)
    payload = build(
        SnippetCommentCreate,
        options.from_file,
        content={"raw": options.content} if options.content is not None else None,
        parent={"id": options.parent} if options.parent is not None else None,
    )
    comments = app_context.workspace().snippet(options.snippet_id).comments
    app_context.render(single(comments.create(payload), COMMENTS, id_key="id"))


@APP.command(help="Edit a comment.")
@handle_errors
@options_from(_UpdateOptions)
def update(ctx: typer.Context, options: _UpdateOptions) -> None:
    app_context = get_app_context(ctx)
    payload = build(
        CommentUpdate,
        options.from_file,
        content={"raw": options.content} if options.content is not None else None,
    )
    comments = app_context.workspace().snippet(options.snippet_id).comments
    app_context.render(single(comments.update(options.comment_id, payload), COMMENTS, id_key="id"))


@APP.command(help="Delete a comment.")
@handle_errors
def delete(ctx: typer.Context, snippet_id: SnippetId, comment_id: CommentId, *, yes: Yes = False) -> None:
    app_context = get_app_context(ctx)
    app_context.confirm(f"Delete comment {comment_id}?", assume_yes=yes)
    app_context.workspace().snippet(snippet_id).comments.delete(comment_id)
    app_context.notify(f"Deleted comment {comment_id}.")

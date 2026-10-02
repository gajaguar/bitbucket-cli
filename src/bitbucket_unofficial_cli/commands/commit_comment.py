from dataclasses import dataclass
from typing import Annotated
from typing import Final

import typer
from bitbucket.models.comment import CommentCreate
from bitbucket.models.comment import CommentUpdate

from bitbucket_unofficial_cli.output.columns import COMMENTS
from bitbucket_unofficial_cli.output.renderer import many
from bitbucket_unofficial_cli.output.renderer import single
from bitbucket_unofficial_cli.runtime.context import get_app_context
from bitbucket_unofficial_cli.runtime.errors import handle_errors
from bitbucket_unofficial_cli.runtime.params import FromFile
from bitbucket_unofficial_cli.runtime.params import PagingOptions
from bitbucket_unofficial_cli.runtime.params import Repo
from bitbucket_unofficial_cli.runtime.params import Yes
from bitbucket_unofficial_cli.runtime.params import options_from
from bitbucket_unofficial_cli.services.listing import paged
from bitbucket_unofficial_cli.services.payloads import build

APP: Final = typer.Typer(help="Comment on a commit.", no_args_is_help=True)

CommitHash = Annotated[str, typer.Argument(help="Commit hash.")]  # pylint: disable=gajaguar-module-const-naming,gajaguar-require-final
CommentId = Annotated[int, typer.Argument(help="Comment ID.")]  # pylint: disable=gajaguar-module-const-naming,gajaguar-require-final
_Content = Annotated[str | None, typer.Option("--content", "-m", help="Comment text.")]  # pylint: disable=gajaguar-module-const-naming,gajaguar-require-final


@dataclass(frozen=True, slots=True, kw_only=True)
class _ListOptions(PagingOptions):
    repo: Repo
    commit: CommitHash


@dataclass(frozen=True, slots=True, kw_only=True)
class _CreateOptions:
    repo: Repo
    commit: CommitHash
    content: _Content = None
    inline_path: Annotated[str | None, typer.Option("--inline-path", help="File to attach the comment to.")] = None
    inline_to: Annotated[int | None, typer.Option("--inline-to", help="Line in the new version.")] = None
    inline_from: Annotated[int | None, typer.Option("--inline-from", help="Line in the old version.")] = None
    parent: Annotated[int | None, typer.Option("--parent", help="Comment ID to reply to.")] = None
    from_file: FromFile = None


@dataclass(frozen=True, slots=True, kw_only=True)
class _UpdateOptions:
    repo: Repo
    commit: CommitHash
    comment_id: CommentId
    content: _Content = None
    from_file: FromFile = None


def _inline(options: _CreateOptions) -> dict[str, object] | None:
    if options.inline_path is None:
        return None
    inline = {"path": options.inline_path, "to": options.inline_to, "from": options.inline_from}
    return {name: value for name, value in inline.items() if value is not None}


@APP.command(name="list", help="List the comments of a commit.")
@handle_errors
@options_from(_ListOptions)
def list_comments(ctx: typer.Context, options: _ListOptions) -> None:
    app_context = get_app_context(ctx)
    comments = app_context.repository(options.repo).commits.comments(options.commit)
    found = paged(app_context, options, comments.list, comments.list_page)
    app_context.render(many(found, COMMENTS, id_key="id"))


@APP.command(help="Show a comment.")
@handle_errors
def get(ctx: typer.Context, commit: CommitHash, comment_id: CommentId, repo: Repo) -> None:
    app_context = get_app_context(ctx)
    comment = app_context.repository(repo).commits.comments(commit).get(comment_id)
    app_context.render(single(comment, COMMENTS, id_key="id"))


@APP.command(help="Add a comment, optionally inline or as a reply.")
@handle_errors
@options_from(_CreateOptions)
def create(ctx: typer.Context, options: _CreateOptions) -> None:
    app_context = get_app_context(ctx)
    payload = build(
        CommentCreate,
        options.from_file,
        content={"raw": options.content} if options.content is not None else None,
        inline=_inline(options),
        parent={"id": options.parent} if options.parent is not None else None,
    )
    comments = app_context.repository(options.repo).commits.comments(options.commit)
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
    comments = app_context.repository(options.repo).commits.comments(options.commit)
    app_context.render(single(comments.update(options.comment_id, payload), COMMENTS, id_key="id"))


@APP.command(help="Delete a comment.")
@handle_errors
def delete(ctx: typer.Context, commit: CommitHash, comment_id: CommentId, repo: Repo, *, yes: Yes = False) -> None:
    app_context = get_app_context(ctx)
    app_context.confirm(f"Delete comment {comment_id}?", assume_yes=yes)
    app_context.repository(repo).commits.comments(commit).delete(comment_id)
    app_context.notify(f"Deleted comment {comment_id}.")

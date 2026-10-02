from dataclasses import dataclass
from typing import Annotated
from typing import Final

import typer
from bitbucket.models.tag import TagCreate

from bitbucket_unofficial_cli.output.columns import TAGS
from bitbucket_unofficial_cli.output.renderer import many
from bitbucket_unofficial_cli.output.renderer import single
from bitbucket_unofficial_cli.runtime.context import get_app_context
from bitbucket_unofficial_cli.runtime.errors import handle_errors
from bitbucket_unofficial_cli.runtime.params import PagingOptions
from bitbucket_unofficial_cli.runtime.params import Repo
from bitbucket_unofficial_cli.runtime.params import Yes
from bitbucket_unofficial_cli.runtime.params import options_from
from bitbucket_unofficial_cli.services.listing import paged
from bitbucket_unofficial_cli.services.payloads import build

APP: Final = typer.Typer(help="Manage the tags of a repository.", no_args_is_help=True)

Name = Annotated[str, typer.Argument(help="Tag name.")]  # pylint: disable=gajaguar-module-const-naming,gajaguar-require-final


@dataclass(frozen=True, slots=True, kw_only=True)
class _ListOptions(PagingOptions):
    repo: Repo


@APP.command(name="list", help="List the tags of a repository.")
@handle_errors
@options_from(_ListOptions)
def list_tags(ctx: typer.Context, options: _ListOptions) -> None:
    app_context = get_app_context(ctx)
    tags = app_context.repository(options.repo).refs.tags
    found = paged(app_context, options, tags.list, tags.list_page)
    app_context.render(many(found, TAGS, id_key="name"))


@APP.command(help="Show a tag.")
@handle_errors
def get(ctx: typer.Context, name: Name, repo: Repo) -> None:
    app_context = get_app_context(ctx)
    app_context.render(single(app_context.repository(repo).refs.tags.get(name), TAGS, id_key="name"))


@APP.command(help="Create a tag at a commit.")
@handle_errors
def create(
    ctx: typer.Context,
    name: Name,
    repo: Repo,
    target: Annotated[str, typer.Option("--target", help="Commit hash to tag.")],
    message: Annotated[str | None, typer.Option("--message", "-m", help="Tag message.")] = None,
) -> None:
    app_context = get_app_context(ctx)
    payload = build(TagCreate, name=name, target={"hash": target}, message=message)
    app_context.render(single(app_context.repository(repo).refs.tags.create(payload), TAGS, id_key="name"))


@APP.command(help="Delete a tag.")
@handle_errors
def delete(ctx: typer.Context, name: Name, repo: Repo, *, yes: Yes = False) -> None:
    app_context = get_app_context(ctx)
    app_context.confirm(f"Delete tag '{name}'?", assume_yes=yes)
    app_context.repository(repo).refs.tags.delete(name)
    app_context.notify(f"Deleted tag '{name}'.")

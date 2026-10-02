from dataclasses import dataclass
from typing import Annotated
from typing import Final

import typer

from bitbucket_unofficial_cli.output.columns import REPOSITORIES
from bitbucket_unofficial_cli.output.columns import REPOSITORY
from bitbucket_unofficial_cli.output.renderer import many
from bitbucket_unofficial_cli.output.renderer import single
from bitbucket_unofficial_cli.runtime.context import get_app_context
from bitbucket_unofficial_cli.runtime.errors import handle_errors
from bitbucket_unofficial_cli.runtime.params import PagingOptions
from bitbucket_unofficial_cli.runtime.params import options_from
from bitbucket_unofficial_cli.services.listing import ListOptions
from bitbucket_unofficial_cli.services.listing import collect

APP: Final = typer.Typer(help="Inspect repositories in the selected workspace.", no_args_is_help=True)


@dataclass(frozen=True, slots=True, kw_only=True)
class _ListOptions(PagingOptions):
    query: Annotated[
        str | None,
        typer.Option("--query", "-q", help="Bitbucket query filter, e.g. 'is_private=true'."),
    ] = None
    sort: Annotated[str | None, typer.Option("--sort", help="Field to sort by; prefix with - to reverse.")] = None


@APP.command(name="list", help="List the repositories of the selected workspace.")
@handle_errors
@options_from(_ListOptions)
def list_repositories(ctx: typer.Context, options: _ListOptions) -> None:
    app_context = get_app_context(ctx)
    repositories = app_context.workspace().repositories
    found = collect(
        lambda: repositories.list(q=options.query, sort=options.sort),
        lambda **page: repositories.list_page(q=options.query, sort=options.sort, **page),
        ListOptions(limit=options.limit, cursor=options.cursor),
        on_next=lambda cursor: app_context.notify(f"next cursor: {cursor}"),
    )
    app_context.render(many(found, REPOSITORIES, id_key="slug"))


@APP.command(help="Show a repository by slug.")
@handle_errors
def get(ctx: typer.Context, slug: Annotated[str, typer.Argument(help="Repository slug.")]) -> None:
    app_context = get_app_context(ctx)
    repository = app_context.workspace().repositories.get(slug)
    app_context.render(single(repository, REPOSITORY, id_key="slug"))

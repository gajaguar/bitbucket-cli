from dataclasses import dataclass
from typing import Final

import typer

from bitbucket_unofficial_cli.output.columns import REFS
from bitbucket_unofficial_cli.output.renderer import many
from bitbucket_unofficial_cli.runtime.context import get_app_context
from bitbucket_unofficial_cli.runtime.errors import handle_errors
from bitbucket_unofficial_cli.runtime.params import PagingOptions
from bitbucket_unofficial_cli.runtime.params import Repo
from bitbucket_unofficial_cli.runtime.params import options_from
from bitbucket_unofficial_cli.services.listing import paged

APP: Final = typer.Typer(help="List the branches and tags of a repository together.", no_args_is_help=True)


@dataclass(frozen=True, slots=True, kw_only=True)
class _ListOptions(PagingOptions):
    repo: Repo


@APP.command(name="list", help="List every branch and tag.")
@handle_errors
@options_from(_ListOptions)
def list_refs(ctx: typer.Context, options: _ListOptions) -> None:
    app_context = get_app_context(ctx)
    refs = app_context.repository(options.repo).refs
    found = paged(app_context, options, refs.list, refs.list_page)
    app_context.render(many(found, REFS, id_key="name"))

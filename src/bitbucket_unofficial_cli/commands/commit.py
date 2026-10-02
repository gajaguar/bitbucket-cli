from dataclasses import dataclass
from typing import Annotated
from typing import Final

import typer

from bitbucket_unofficial_cli.output.columns import PULL_REQUESTS
from bitbucket_unofficial_cli.output.renderer import many
from bitbucket_unofficial_cli.runtime.context import get_app_context
from bitbucket_unofficial_cli.runtime.errors import handle_errors
from bitbucket_unofficial_cli.runtime.params import PagingOptions
from bitbucket_unofficial_cli.runtime.params import Repo
from bitbucket_unofficial_cli.runtime.params import options_from
from bitbucket_unofficial_cli.services.listing import paged

APP: Final = typer.Typer(help="Work with the commits of a repository.", no_args_is_help=True)


@dataclass(frozen=True, slots=True, kw_only=True)
class _PrsOptions(PagingOptions):
    repo: Repo
    commit: Annotated[str, typer.Argument(help="Commit hash.")]


@APP.command(help="List the pull requests that contain a commit.")
@handle_errors
@options_from(_PrsOptions)
def prs(ctx: typer.Context, options: _PrsOptions) -> None:
    app_context = get_app_context(ctx)
    repositories = app_context.workspace().repositories
    found = paged(
        app_context,
        options,
        lambda: repositories.commit_pull_requests(options.repo, options.commit),
        lambda **page: repositories.commit_pull_requests_page(options.repo, options.commit, **page),
    )
    app_context.render(many(found, PULL_REQUESTS, id_key="id"))

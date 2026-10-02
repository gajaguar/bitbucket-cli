from dataclasses import dataclass
from typing import Annotated
from typing import Final

import typer

from bitbucket_unofficial_cli.output.columns import DEPLOYMENTS
from bitbucket_unofficial_cli.output.renderer import many
from bitbucket_unofficial_cli.output.renderer import single
from bitbucket_unofficial_cli.runtime.context import get_app_context
from bitbucket_unofficial_cli.runtime.errors import handle_errors
from bitbucket_unofficial_cli.runtime.params import PagingOptions
from bitbucket_unofficial_cli.runtime.params import Repo
from bitbucket_unofficial_cli.runtime.params import options_from
from bitbucket_unofficial_cli.services.listing import paged

APP: Final = typer.Typer(help="Inspect the deployments of a repository.", no_args_is_help=True)


@dataclass(frozen=True, slots=True, kw_only=True)
class _ListOptions(PagingOptions):
    repo: Repo


@APP.command(name="list", help="List the deployments of a repository.")
@handle_errors
@options_from(_ListOptions)
def list_deployments(ctx: typer.Context, options: _ListOptions) -> None:
    app_context = get_app_context(ctx)
    deployments = app_context.repository(options.repo).deployments
    found = paged(app_context, options, deployments.list, deployments.list_page)
    app_context.render(many(found, DEPLOYMENTS, id_key="uuid"))


@APP.command(help="Show a deployment.")
@handle_errors
def get(ctx: typer.Context, uuid: Annotated[str, typer.Argument(help="Deployment UUID.")], repo: Repo) -> None:
    app_context = get_app_context(ctx)
    app_context.render(single(app_context.repository(repo).deployments.get(uuid), DEPLOYMENTS, id_key="uuid"))

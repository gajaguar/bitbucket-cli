from dataclasses import dataclass
from typing import Annotated
from typing import Final

import typer
from bitbucket import ProjectClient

from bitbucket_unofficial_cli.output.columns import DEFAULT_REVIEWERS
from bitbucket_unofficial_cli.output.columns import PROJECT_DEFAULT_REVIEWERS
from bitbucket_unofficial_cli.output.renderer import many
from bitbucket_unofficial_cli.output.renderer import single
from bitbucket_unofficial_cli.runtime.context import get_app_context
from bitbucket_unofficial_cli.runtime.errors import CliError
from bitbucket_unofficial_cli.runtime.errors import handle_errors
from bitbucket_unofficial_cli.runtime.exit_codes import ExitCode
from bitbucket_unofficial_cli.runtime.params import OptionalRepo
from bitbucket_unofficial_cli.runtime.params import PagingOptions
from bitbucket_unofficial_cli.runtime.params import ProjectScope
from bitbucket_unofficial_cli.runtime.params import options_from
from bitbucket_unofficial_cli.runtime.scope import resolve_scope
from bitbucket_unofficial_cli.services.listing import paged

APP: Final = typer.Typer(help="Manage the default reviewers of a repository or project.", no_args_is_help=True)

User = Annotated[str, typer.Argument(help="Account ID or UUID of the user.")]  # pylint: disable=gajaguar-module-const-naming,gajaguar-require-final


@dataclass(frozen=True, slots=True, kw_only=True)
class _ListOptions(PagingOptions):
    repo: OptionalRepo = None
    project: ProjectScope = None


@dataclass(frozen=True, slots=True, kw_only=True)
class _UserOptions:
    user: User
    repo: OptionalRepo = None
    project: ProjectScope = None


@APP.command(name="list", help="List the default reviewers.")
@handle_errors
@options_from(_ListOptions)
def list_reviewers(ctx: typer.Context, options: _ListOptions) -> None:
    app_context = get_app_context(ctx)
    client = resolve_scope(ctx, app_context, options.repo, options.project)
    if isinstance(client, ProjectClient):
        project_reviewers = client.default_reviewers
        found = paged(app_context, options, project_reviewers.list, project_reviewers.list_page)
        app_context.render(many(found, PROJECT_DEFAULT_REVIEWERS, id_key="user.account_id"))
    else:
        reviewers = client.default_reviewers
        repo_found = paged(app_context, options, reviewers.list, reviewers.list_page)
        app_context.render(many(repo_found, DEFAULT_REVIEWERS, id_key="account_id"))


@APP.command(help="Show one default reviewer.")
@handle_errors
@options_from(_UserOptions)
def get(ctx: typer.Context, options: _UserOptions) -> None:
    app_context = get_app_context(ctx)
    client = resolve_scope(ctx, app_context, options.repo, options.project)
    app_context.render(single(client.default_reviewers.get(options.user), DEFAULT_REVIEWERS, id_key="account_id"))


@APP.command(help="Add a default reviewer.")
@handle_errors
@options_from(_UserOptions)
def add(ctx: typer.Context, options: _UserOptions) -> None:
    app_context = get_app_context(ctx)
    client = resolve_scope(ctx, app_context, options.repo, options.project)
    app_context.render(single(client.default_reviewers.add(options.user), DEFAULT_REVIEWERS, id_key="account_id"))


@APP.command(help="Remove a default reviewer.")
@handle_errors
@options_from(_UserOptions)
def remove(ctx: typer.Context, options: _UserOptions) -> None:
    app_context = get_app_context(ctx)
    client = resolve_scope(ctx, app_context, options.repo, options.project)
    client.default_reviewers.remove(options.user)
    app_context.notify(f"Removed default reviewer '{options.user}'.")


@APP.command(help="List the reviewers a repository effectively uses, project defaults included.")
@handle_errors
@options_from(_ListOptions)
def effective(ctx: typer.Context, options: _ListOptions) -> None:
    app_context = get_app_context(ctx)
    client = resolve_scope(ctx, app_context, options.repo, options.project)
    if isinstance(client, ProjectClient):
        message = "A project has no effective default reviewers; use --repo."
        raise CliError(message, exit_code=ExitCode.USAGE)
    reviewers = client.default_reviewers
    found = paged(app_context, options, reviewers.effective, reviewers.effective_page)
    app_context.render(many(found, DEFAULT_REVIEWERS, id_key="account_id"))

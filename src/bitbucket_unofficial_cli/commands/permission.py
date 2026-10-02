from dataclasses import dataclass
from typing import Annotated
from typing import Final

import typer

from bitbucket_unofficial_cli.output.columns import MEMBERS
from bitbucket_unofficial_cli.output.columns import REPOSITORY_PERMISSIONS
from bitbucket_unofficial_cli.output.renderer import many
from bitbucket_unofficial_cli.output.renderer import single
from bitbucket_unofficial_cli.runtime.context import get_app_context
from bitbucket_unofficial_cli.runtime.errors import CliError
from bitbucket_unofficial_cli.runtime.errors import handle_errors
from bitbucket_unofficial_cli.runtime.exit_codes import ExitCode
from bitbucket_unofficial_cli.runtime.params import QueryOptions
from bitbucket_unofficial_cli.runtime.params import options_from
from bitbucket_unofficial_cli.services.listing import paged

APP: Final = typer.Typer(help="Inspect workspace permissions.", no_args_is_help=True)


@dataclass(frozen=True, slots=True, kw_only=True)
class _MineOptions(QueryOptions):
    repositories: Annotated[
        bool,
        typer.Option("--repositories", help="List your permission on each repository instead of the workspace."),
    ] = False


@dataclass(frozen=True, slots=True, kw_only=True)
class _ListOptions(QueryOptions):
    repositories: Annotated[
        bool,
        typer.Option("--repositories", help="List the permission of every user on every repository."),
    ] = False
    repository: Annotated[
        str | None,
        typer.Option("--repository", help="List the permissions on this repository slug."),
    ] = None


@APP.command(help="Show your permission on the workspace, or on its repositories.")
@handle_errors
@options_from(_MineOptions)
def mine(ctx: typer.Context, options: _MineOptions) -> None:
    app_context = get_app_context(ctx)
    workspace = app_context.workspace()
    if not options.repositories:
        app_context.render(single(workspace.my_permission(), MEMBERS, id_key="user.account_id"))
        return
    found = paged(
        app_context,
        options,
        lambda: workspace.my_repository_permissions(q=options.query, sort=options.sort),
        lambda **page: workspace.my_repository_permissions_page(q=options.query, sort=options.sort, **page),
    )
    app_context.render(many(found, REPOSITORY_PERMISSIONS, id_key="repository.slug"))


@APP.command(name="list", help="List the effective permissions in the workspace.")
@handle_errors
@options_from(_ListOptions)
def list_permissions(ctx: typer.Context, options: _ListOptions) -> None:
    app_context = get_app_context(ctx)
    if options.repositories and options.repository:
        message = "--repositories and --repository cannot be combined."
        raise CliError(message, exit_code=ExitCode.USAGE)
    permissions = app_context.workspace().permissions
    if options.repository:
        slug = options.repository
        found = paged(
            app_context,
            options,
            lambda: permissions.repository(slug, q=options.query, sort=options.sort),
            lambda **page: permissions.repository_page(slug, q=options.query, sort=options.sort, **page),
        )
        app_context.render(many(found, REPOSITORY_PERMISSIONS, id_key="user.account_id"))
    elif options.repositories:
        found = paged(
            app_context,
            options,
            lambda: permissions.repositories(q=options.query, sort=options.sort),
            lambda **page: permissions.repositories_page(q=options.query, sort=options.sort, **page),
        )
        app_context.render(many(found, REPOSITORY_PERMISSIONS, id_key="repository.slug"))
    else:
        members = paged(
            app_context,
            options,
            lambda: permissions.list(q=options.query),
            lambda **page: permissions.list_page(q=options.query, **page),
        )
        app_context.render(many(members, MEMBERS, id_key="user.account_id"))

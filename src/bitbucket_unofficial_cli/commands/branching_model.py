from dataclasses import dataclass
from typing import Annotated
from typing import Final

import typer
from bitbucket import ProjectClient
from bitbucket.models.branching_model import BranchingModelSettingsUpdate

from bitbucket_unofficial_cli.output.columns import BRANCHING_MODEL
from bitbucket_unofficial_cli.output.columns import BRANCHING_SETTINGS
from bitbucket_unofficial_cli.output.renderer import single
from bitbucket_unofficial_cli.runtime.context import get_app_context
from bitbucket_unofficial_cli.runtime.errors import CliError
from bitbucket_unofficial_cli.runtime.errors import handle_errors
from bitbucket_unofficial_cli.runtime.exit_codes import ExitCode
from bitbucket_unofficial_cli.runtime.params import FromFile
from bitbucket_unofficial_cli.runtime.params import OptionalRepo
from bitbucket_unofficial_cli.runtime.params import ProjectScope
from bitbucket_unofficial_cli.runtime.params import options_from
from bitbucket_unofficial_cli.runtime.scope import resolve_scope
from bitbucket_unofficial_cli.services.payloads import build

APP: Final = typer.Typer(
    help="Show and configure the branching model of a repository or project.", no_args_is_help=True
)


@dataclass(frozen=True, slots=True, kw_only=True)
class _ScopeOptions:
    repo: OptionalRepo = None
    project: ProjectScope = None


@dataclass(frozen=True, slots=True, kw_only=True)
class _UpdateOptions(_ScopeOptions):
    development_name: Annotated[str | None, typer.Option("--development-name", help="Development branch.")] = None
    development_main: Annotated[
        bool | None,
        typer.Option("--development-main/--no-development-main", help="Use the main branch for development."),
    ] = None
    production_name: Annotated[str | None, typer.Option("--production-name", help="Production branch.")] = None
    production_main: Annotated[
        bool | None,
        typer.Option("--production-main/--no-production-main", help="Use the main branch for production."),
    ] = None
    production_enabled: Annotated[
        bool | None,
        typer.Option("--production/--no-production", help="Enable the production branch."),
    ] = None
    from_file: FromFile = None


def _section(*, name: str | None, use_main: bool | None, enabled: bool | None = None) -> dict[str, object] | None:
    section: dict[str, object] = {"name": name, "use_mainbranch": use_main, "enabled": enabled}
    present = {key: value for key, value in section.items() if value is not None}
    return present or None


@APP.command(help="Show the branching model.")
@handle_errors
@options_from(_ScopeOptions)
def get(ctx: typer.Context, options: _ScopeOptions) -> None:
    app_context = get_app_context(ctx)
    client = resolve_scope(ctx, app_context, options.repo, options.project)
    app_context.render(single(client.branching_model.get(), BRANCHING_MODEL, id_key="development.name"))


@APP.command(help="Show the branching model settings.")
@handle_errors
@options_from(_ScopeOptions)
def settings(ctx: typer.Context, options: _ScopeOptions) -> None:
    app_context = get_app_context(ctx)
    client = resolve_scope(ctx, app_context, options.repo, options.project)
    app_context.render(single(client.branching_model.settings(), BRANCHING_SETTINGS, id_key="development.name"))


@APP.command(help="Change the branching model settings.")
@handle_errors
@options_from(_UpdateOptions)
def update(ctx: typer.Context, options: _UpdateOptions) -> None:
    app_context = get_app_context(ctx)
    client = resolve_scope(ctx, app_context, options.repo, options.project)
    payload = build(
        BranchingModelSettingsUpdate,
        options.from_file,
        development=_section(name=options.development_name, use_main=options.development_main),
        production=_section(
            name=options.production_name, use_main=options.production_main, enabled=options.production_enabled
        ),
    )
    updated = client.branching_model.update_settings(payload)
    app_context.render(single(updated, BRANCHING_SETTINGS, id_key="development.name"))


@APP.command(help="Show the branching model a repository effectively uses.")
@handle_errors
@options_from(_ScopeOptions)
def effective(ctx: typer.Context, options: _ScopeOptions) -> None:
    app_context = get_app_context(ctx)
    client = resolve_scope(ctx, app_context, options.repo, options.project)
    if isinstance(client, ProjectClient):
        message = "A project has no effective branching model; use --repo."
        raise CliError(message, exit_code=ExitCode.USAGE)
    app_context.render(single(client.branching_model.effective(), BRANCHING_MODEL, id_key="development.name"))

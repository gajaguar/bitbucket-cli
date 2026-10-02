from dataclasses import dataclass
from typing import TYPE_CHECKING
from typing import Annotated
from typing import Final

import typer
from bitbucket.models.pipeline_variable import PipelineVariableCreate
from bitbucket.models.pipeline_variable import PipelineVariableUpdate

from bitbucket_unofficial_cli.output.columns import PIPELINE_VARIABLES
from bitbucket_unofficial_cli.output.renderer import many
from bitbucket_unofficial_cli.output.renderer import single
from bitbucket_unofficial_cli.runtime.context import AppContext
from bitbucket_unofficial_cli.runtime.context import get_app_context
from bitbucket_unofficial_cli.runtime.errors import handle_errors
from bitbucket_unofficial_cli.runtime.params import OptionalRepo
from bitbucket_unofficial_cli.runtime.params import PagingOptions
from bitbucket_unofficial_cli.runtime.params import options_from
from bitbucket_unofficial_cli.services.listing import paged
from bitbucket_unofficial_cli.services.payloads import build
from bitbucket_unofficial_cli.services.secrets import read_secret

if TYPE_CHECKING:
    from bitbucket.resources.pipeline_variables import PipelineVariablesResource

APP: Final = typer.Typer(
    help="Pipeline variables of a repository (--repo), or of the workspace without it.", no_args_is_help=True
)

Uuid = Annotated[str, typer.Argument(help="Variable UUID.")]  # pylint: disable=gajaguar-module-const-naming,gajaguar-require-final
_Secured = Annotated[bool | None, typer.Option("--secured/--unsecured", help="Hide the value once stored.")]  # pylint: disable=gajaguar-module-const-naming,gajaguar-require-final


def variables_of(app_context: AppContext, repo: str | None) -> PipelineVariablesResource:
    if repo:
        return app_context.repository(repo).pipelines_config.variables
    return app_context.workspace().pipelines_config.variables


@dataclass(frozen=True, slots=True, kw_only=True)
class _ListOptions(PagingOptions):
    repo: OptionalRepo = None


@dataclass(frozen=True, slots=True, kw_only=True)
class _CreateOptions:
    key: Annotated[str, typer.Argument(help="Variable name.")]
    repo: OptionalRepo = None
    stdin: Annotated[bool, typer.Option("--stdin", help="Read the value from stdin instead of asking.")] = False
    secured: _Secured = None


@dataclass(frozen=True, slots=True, kw_only=True)
class _UpdateOptions:
    uuid: Uuid
    repo: OptionalRepo = None
    key: Annotated[str | None, typer.Option("--key", help="Rename the variable.")] = None
    stdin: Annotated[bool, typer.Option("--stdin", help="Read a new value from stdin.")] = False
    secured: _Secured = None


@dataclass(frozen=True, slots=True, kw_only=True)
class _DeleteOptions:
    uuid: Uuid
    repo: OptionalRepo = None
    yes: Annotated[bool, typer.Option("--yes", "-y", help="Do not ask for confirmation.")] = False


@APP.command(name="list", help="List pipeline variables. Stored values are never printed.")
@handle_errors
@options_from(_ListOptions)
def list_variables(ctx: typer.Context, options: _ListOptions) -> None:
    app_context = get_app_context(ctx)
    variables = variables_of(app_context, options.repo)
    found = paged(app_context, options, variables.list, variables.list_page)
    app_context.render(many(found, PIPELINE_VARIABLES, id_key="uuid"))


@APP.command(help="Show a pipeline variable.")
@handle_errors
def get(ctx: typer.Context, uuid: Uuid, repo: OptionalRepo = None) -> None:
    app_context = get_app_context(ctx)
    app_context.render(single(variables_of(app_context, repo).get(uuid), PIPELINE_VARIABLES, id_key="uuid"))


@APP.command(help="Add a variable; the value is asked for, or read from stdin.")
@handle_errors
@options_from(_CreateOptions)
def create(ctx: typer.Context, options: _CreateOptions) -> None:
    app_context = get_app_context(ctx)
    value = read_secret(f"Value of {options.key}", from_stdin=options.stdin)
    payload = build(PipelineVariableCreate, key=options.key, value=value, secured=options.secured)
    app_context.render(
        single(variables_of(app_context, options.repo).create(payload), PIPELINE_VARIABLES, id_key="uuid")
    )


@APP.command(help="Change a variable; a new value is read from stdin with --stdin.")
@handle_errors
@options_from(_UpdateOptions)
def update(ctx: typer.Context, options: _UpdateOptions) -> None:
    app_context = get_app_context(ctx)
    value = read_secret("New value", from_stdin=True) if options.stdin else None
    payload = build(PipelineVariableUpdate, key=options.key, value=value, secured=options.secured)
    updated = variables_of(app_context, options.repo).update(options.uuid, payload)
    app_context.render(single(updated, PIPELINE_VARIABLES, id_key="uuid"))


@APP.command(help="Delete a variable.")
@handle_errors
@options_from(_DeleteOptions)
def delete(ctx: typer.Context, options: _DeleteOptions) -> None:
    app_context = get_app_context(ctx)
    app_context.confirm(f"Delete variable '{options.uuid}'?", assume_yes=options.yes)
    variables_of(app_context, options.repo).delete(options.uuid)
    app_context.notify(f"Deleted variable '{options.uuid}'.")

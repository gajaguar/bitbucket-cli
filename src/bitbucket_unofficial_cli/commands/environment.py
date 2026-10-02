from dataclasses import dataclass
from typing import Annotated
from typing import Final

import typer
from bitbucket.models.deployment import EnvironmentCreate
from bitbucket.models.deployment import EnvironmentUpdate
from bitbucket.models.pipeline_variable import PipelineVariableCreate
from bitbucket.models.pipeline_variable import PipelineVariableUpdate

from bitbucket_unofficial_cli.output.columns import ENVIRONMENTS
from bitbucket_unofficial_cli.output.columns import PIPELINE_VARIABLES
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
from bitbucket_unofficial_cli.services.secrets import read_secret

APP: Final = typer.Typer(help="Manage the deployment environments of a repository.", no_args_is_help=True)
VARIABLE_APP: Final = typer.Typer(help="Variables of a deployment environment.", no_args_is_help=True)
APP.add_typer(VARIABLE_APP, name="variable")

Uuid = Annotated[str, typer.Argument(help="Environment UUID.")]  # pylint: disable=gajaguar-module-const-naming,gajaguar-require-final
VariableUuid = Annotated[str, typer.Argument(help="Variable UUID.")]  # pylint: disable=gajaguar-module-const-naming,gajaguar-require-final
_Secured = Annotated[bool | None, typer.Option("--secured/--unsecured", help="Hide the value once stored.")]  # pylint: disable=gajaguar-module-const-naming,gajaguar-require-final


@dataclass(frozen=True, slots=True, kw_only=True)
class _ListOptions(PagingOptions):
    repo: Repo


@dataclass(frozen=True, slots=True, kw_only=True)
class _CreateOptions:
    repo: Repo
    name: Annotated[str | None, typer.Option("--name", help="Environment name.")] = None
    from_file: FromFile = None


@dataclass(frozen=True, slots=True, kw_only=True)
class _UpdateOptions(_CreateOptions):
    uuid: Uuid


@dataclass(frozen=True, slots=True, kw_only=True)
class _DeleteOptions:
    repo: Repo
    uuid: Uuid
    yes: Yes = False


@dataclass(frozen=True, slots=True, kw_only=True)
class _VariableListOptions(PagingOptions):
    repo: Repo
    environment: Uuid


@dataclass(frozen=True, slots=True, kw_only=True)
class _VariableCreateOptions:
    repo: Repo
    environment: Uuid
    key: Annotated[str, typer.Argument(help="Variable name.")]
    stdin: Annotated[bool, typer.Option("--stdin", help="Read the value from stdin instead of asking.")] = False
    secured: _Secured = None


@dataclass(frozen=True, slots=True, kw_only=True)
class _VariableUpdateOptions:
    repo: Repo
    environment: Uuid
    uuid: VariableUuid
    key: Annotated[str | None, typer.Option("--key", help="Rename the variable.")] = None
    stdin: Annotated[bool, typer.Option("--stdin", help="Read a new value from stdin.")] = False
    secured: _Secured = None


@dataclass(frozen=True, slots=True, kw_only=True)
class _VariableDeleteOptions:
    repo: Repo
    environment: Uuid
    uuid: VariableUuid
    yes: Yes = False


@APP.command(name="list", help="List the environments of a repository.")
@handle_errors
@options_from(_ListOptions)
def list_environments(ctx: typer.Context, options: _ListOptions) -> None:
    app_context = get_app_context(ctx)
    environments = app_context.repository(options.repo).environments
    found = paged(app_context, options, environments.list, environments.list_page)
    app_context.render(many(found, ENVIRONMENTS, id_key="uuid"))


@APP.command(help="Show an environment.")
@handle_errors
def get(ctx: typer.Context, uuid: Uuid, repo: Repo) -> None:
    app_context = get_app_context(ctx)
    app_context.render(single(app_context.repository(repo).environments.get(uuid), ENVIRONMENTS, id_key="uuid"))


@APP.command(help="Create an environment.")
@handle_errors
@options_from(_CreateOptions)
def create(ctx: typer.Context, options: _CreateOptions) -> None:
    app_context = get_app_context(ctx)
    payload = build(EnvironmentCreate, options.from_file, name=options.name)
    created = app_context.repository(options.repo).environments.create(payload)
    app_context.render(single(created, ENVIRONMENTS, id_key="uuid"))


@APP.command(help="Rename an environment.")
@handle_errors
@options_from(_UpdateOptions)
def update(ctx: typer.Context, options: _UpdateOptions) -> None:
    app_context = get_app_context(ctx)
    payload = build(EnvironmentUpdate, options.from_file, name=options.name)
    environments = app_context.repository(options.repo).environments
    environments.update(options.uuid, payload)
    app_context.render(single(environments.get(options.uuid), ENVIRONMENTS, id_key="uuid"))


@APP.command(help="Delete an environment.")
@handle_errors
@options_from(_DeleteOptions)
def delete(ctx: typer.Context, options: _DeleteOptions) -> None:
    app_context = get_app_context(ctx)
    app_context.confirm(f"Delete environment '{options.uuid}'?", assume_yes=options.yes)
    app_context.repository(options.repo).environments.delete(options.uuid)
    app_context.notify(f"Deleted environment '{options.uuid}'.")


@VARIABLE_APP.command(name="list", help="List the variables of an environment. Stored values are never printed.")
@handle_errors
@options_from(_VariableListOptions)
def list_variables(ctx: typer.Context, options: _VariableListOptions) -> None:
    app_context = get_app_context(ctx)
    variables = app_context.repository(options.repo).environments.variables(options.environment)
    found = paged(app_context, options, variables.list, variables.list_page)
    app_context.render(many(found, PIPELINE_VARIABLES, id_key="uuid"))


@VARIABLE_APP.command(name="create", help="Add a variable; the value is asked for, or read from stdin.")
@handle_errors
@options_from(_VariableCreateOptions)
def create_variable(ctx: typer.Context, options: _VariableCreateOptions) -> None:
    app_context = get_app_context(ctx)
    value = read_secret(f"Value of {options.key}", from_stdin=options.stdin)
    payload = build(PipelineVariableCreate, key=options.key, value=value, secured=options.secured)
    variables = app_context.repository(options.repo).environments.variables(options.environment)
    app_context.render(single(variables.create(payload), PIPELINE_VARIABLES, id_key="uuid"))


@VARIABLE_APP.command(name="update", help="Change a variable; a new value is read from stdin with --stdin.")
@handle_errors
@options_from(_VariableUpdateOptions)
def update_variable(ctx: typer.Context, options: _VariableUpdateOptions) -> None:
    app_context = get_app_context(ctx)
    value = read_secret("New value", from_stdin=True) if options.stdin else None
    payload = build(PipelineVariableUpdate, key=options.key, value=value, secured=options.secured)
    variables = app_context.repository(options.repo).environments.variables(options.environment)
    app_context.render(single(variables.update(options.uuid, payload), PIPELINE_VARIABLES, id_key="uuid"))


@VARIABLE_APP.command(name="delete", help="Delete a variable.")
@handle_errors
@options_from(_VariableDeleteOptions)
def delete_variable(ctx: typer.Context, options: _VariableDeleteOptions) -> None:
    app_context = get_app_context(ctx)
    app_context.confirm(f"Delete variable '{options.uuid}'?", assume_yes=options.yes)
    app_context.repository(options.repo).environments.variables(options.environment).delete(options.uuid)
    app_context.notify(f"Deleted variable '{options.uuid}'.")

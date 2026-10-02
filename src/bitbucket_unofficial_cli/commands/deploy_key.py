from dataclasses import dataclass
from typing import Annotated
from typing import Final

import typer
from bitbucket import ProjectClient
from bitbucket.models.deploy_key import DeployKeyCreate
from bitbucket.models.deploy_key import DeployKeyUpdate

from bitbucket_unofficial_cli.output.columns import DEPLOY_KEYS
from bitbucket_unofficial_cli.output.renderer import many
from bitbucket_unofficial_cli.output.renderer import single
from bitbucket_unofficial_cli.runtime.context import get_app_context
from bitbucket_unofficial_cli.runtime.errors import CliError
from bitbucket_unofficial_cli.runtime.errors import handle_errors
from bitbucket_unofficial_cli.runtime.exit_codes import ExitCode
from bitbucket_unofficial_cli.runtime.params import FromFile
from bitbucket_unofficial_cli.runtime.params import OptionalRepo
from bitbucket_unofficial_cli.runtime.params import PagingOptions
from bitbucket_unofficial_cli.runtime.params import ProjectScope
from bitbucket_unofficial_cli.runtime.params import options_from
from bitbucket_unofficial_cli.runtime.scope import resolve_scope
from bitbucket_unofficial_cli.services.listing import paged
from bitbucket_unofficial_cli.services.payloads import build

APP: Final = typer.Typer(help="Manage the deploy keys of a repository or project.", no_args_is_help=True)

KeyId = Annotated[int, typer.Argument(help="Deploy key ID.")]  # pylint: disable=gajaguar-module-const-naming,gajaguar-require-final


@dataclass(frozen=True, slots=True, kw_only=True)
class _ListOptions(PagingOptions):
    repo: OptionalRepo = None
    project: ProjectScope = None


@dataclass(frozen=True, slots=True, kw_only=True)
class _KeyOptions:
    key_id: KeyId
    repo: OptionalRepo = None
    project: ProjectScope = None


@dataclass(frozen=True, slots=True, kw_only=True)
class _CreateOptions:
    repo: OptionalRepo = None
    project: ProjectScope = None
    key: Annotated[str | None, typer.Option("--key", help="SSH public key.")] = None
    label: Annotated[str | None, typer.Option("--label", help="Label for the key.")] = None
    from_file: FromFile = None


@dataclass(frozen=True, slots=True, kw_only=True)
class _UpdateOptions(_CreateOptions):
    key_id: KeyId


@dataclass(frozen=True, slots=True, kw_only=True)
class _DeleteOptions(_KeyOptions):
    yes: Annotated[bool, typer.Option("--yes", "-y", help="Do not ask for confirmation.")] = False


@APP.command(name="list", help="List the deploy keys.")
@handle_errors
@options_from(_ListOptions)
def list_keys(ctx: typer.Context, options: _ListOptions) -> None:
    app_context = get_app_context(ctx)
    client = resolve_scope(ctx, app_context, options.repo, options.project)
    if isinstance(client, ProjectClient):
        project_keys = client.deploy_keys
        found = paged(app_context, options, project_keys.list, project_keys.list_page)
        app_context.render(many(found, DEPLOY_KEYS, id_key="id"))
    else:
        keys = client.deploy_keys
        repo_found = paged(app_context, options, keys.list, keys.list_page)
        app_context.render(many(repo_found, DEPLOY_KEYS, id_key="id"))


@APP.command(help="Show a deploy key.")
@handle_errors
@options_from(_KeyOptions)
def get(ctx: typer.Context, options: _KeyOptions) -> None:
    app_context = get_app_context(ctx)
    client = resolve_scope(ctx, app_context, options.repo, options.project)
    app_context.render(single(client.deploy_keys.get(options.key_id), DEPLOY_KEYS, id_key="id"))


@APP.command(help="Add a deploy key.")
@handle_errors
@options_from(_CreateOptions)
def create(ctx: typer.Context, options: _CreateOptions) -> None:
    app_context = get_app_context(ctx)
    client = resolve_scope(ctx, app_context, options.repo, options.project)
    payload = build(DeployKeyCreate, options.from_file, key=options.key, label=options.label)
    app_context.render(single(client.deploy_keys.create(payload), DEPLOY_KEYS, id_key="id"))


@APP.command(help="Change the label of a repository deploy key.")
@handle_errors
@options_from(_UpdateOptions)
def update(ctx: typer.Context, options: _UpdateOptions) -> None:
    app_context = get_app_context(ctx)
    client = resolve_scope(ctx, app_context, options.repo, options.project)
    if isinstance(client, ProjectClient):
        message = "Bitbucket cannot update a project deploy key; delete it and add it again."
        raise CliError(message, exit_code=ExitCode.USAGE)
    payload = build(DeployKeyUpdate, options.from_file, key=options.key, label=options.label)
    app_context.render(single(client.deploy_keys.update(options.key_id, payload), DEPLOY_KEYS, id_key="id"))


@APP.command(help="Delete a deploy key.")
@handle_errors
@options_from(_DeleteOptions)
def delete(ctx: typer.Context, options: _DeleteOptions) -> None:
    app_context = get_app_context(ctx)
    client = resolve_scope(ctx, app_context, options.repo, options.project)
    app_context.confirm(f"Delete deploy key {options.key_id}?", assume_yes=options.yes)
    client.deploy_keys.delete(options.key_id)
    app_context.notify(f"Deleted deploy key {options.key_id}.")

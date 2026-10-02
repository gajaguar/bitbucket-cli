import json
from dataclasses import dataclass
from enum import StrEnum
from typing import Annotated
from typing import Final

import typer
from bitbucket.models.status import CommitStatusCreate
from bitbucket.models.status import CommitStatusUpdate

from bitbucket_unofficial_cli.output.columns import PULL_REQUEST_STATUSES
from bitbucket_unofficial_cli.output.renderer import many
from bitbucket_unofficial_cli.output.renderer import single
from bitbucket_unofficial_cli.runtime.context import get_app_context
from bitbucket_unofficial_cli.runtime.errors import handle_errors
from bitbucket_unofficial_cli.runtime.params import FromFile
from bitbucket_unofficial_cli.runtime.params import PagingOptions
from bitbucket_unofficial_cli.runtime.params import Repo
from bitbucket_unofficial_cli.runtime.params import options_from
from bitbucket_unofficial_cli.services.jsonvalue import parse_value
from bitbucket_unofficial_cli.services.listing import paged
from bitbucket_unofficial_cli.services.payloads import build

STATUS_APP: Final = typer.Typer(help="Build statuses reported on a commit.", no_args_is_help=True)
PROPERTY_APP: Final = typer.Typer(help="Connect app properties of a commit.", no_args_is_help=True)

CommitHash = Annotated[str, typer.Argument(help="Commit hash.")]  # pylint: disable=gajaguar-module-const-naming,gajaguar-require-final
Key = Annotated[str, typer.Argument(help="Status key.")]  # pylint: disable=gajaguar-module-const-naming,gajaguar-require-final
AppKey = Annotated[str, typer.Argument(help="Connect app key.")]  # pylint: disable=gajaguar-module-const-naming,gajaguar-require-final
Name = Annotated[str, typer.Argument(help="Property name.")]  # pylint: disable=gajaguar-module-const-naming,gajaguar-require-final


class _State(StrEnum):
    FAILED = "FAILED"
    INPROGRESS = "INPROGRESS"
    STOPPED = "STOPPED"
    SUCCESSFUL = "SUCCESSFUL"


@dataclass(frozen=True, slots=True, kw_only=True)
class _ListOptions(PagingOptions):
    repo: Repo
    commit: CommitHash


@dataclass(frozen=True, slots=True, kw_only=True)
class _CreateOptions:
    repo: Repo
    commit: CommitHash
    key: Annotated[str | None, typer.Option("--key", help="Unique key of the status.")] = None
    state: Annotated[_State | None, typer.Option("--state", help="Build state.")] = None
    url: Annotated[str | None, typer.Option("--url", help="Link to the build.")] = None
    name: Annotated[str | None, typer.Option("--name", help="Display name.")] = None
    description: Annotated[str | None, typer.Option("--description", help="What the build did.")] = None
    from_file: FromFile = None


@dataclass(frozen=True, slots=True, kw_only=True)
class _UpdateOptions(_CreateOptions):
    status_key: Key


@dataclass(frozen=True, slots=True, kw_only=True)
class _SetOptions:
    repo: Repo
    commit: CommitHash
    app_key: AppKey
    name: Name
    value: Annotated[str, typer.Argument(help="JSON value, or - for stdin.")]


@STATUS_APP.command(name="list", help="List the build statuses of a commit.")
@handle_errors
@options_from(_ListOptions)
def list_statuses(ctx: typer.Context, options: _ListOptions) -> None:
    app_context = get_app_context(ctx)
    statuses = app_context.repository(options.repo).commit_statuses
    found = paged(
        app_context,
        options,
        lambda: statuses.list(options.commit),
        lambda **page: statuses.list_page(options.commit, **page),
    )
    app_context.render(many(found, PULL_REQUEST_STATUSES, id_key="key"))


@STATUS_APP.command(name="get", help="Show one build status.")
@handle_errors
def get_status(ctx: typer.Context, commit: CommitHash, key: Key, repo: Repo) -> None:
    app_context = get_app_context(ctx)
    status = app_context.repository(repo).commit_statuses.get(commit, key)
    app_context.render(single(status, PULL_REQUEST_STATUSES, id_key="key"))


@STATUS_APP.command(name="create", help="Report a build status for a commit.")
@handle_errors
@options_from(_CreateOptions)
def create_status(ctx: typer.Context, options: _CreateOptions) -> None:
    app_context = get_app_context(ctx)
    payload = build(
        CommitStatusCreate,
        options.from_file,
        key=options.key,
        state=options.state.value if options.state else None,
        url=options.url,
        name=options.name,
        description=options.description,
    )
    status = app_context.repository(options.repo).commit_statuses.create(options.commit, payload)
    app_context.render(single(status, PULL_REQUEST_STATUSES, id_key="key"))


@STATUS_APP.command(name="update", help="Change a build status.")
@handle_errors
@options_from(_UpdateOptions)
def update_status(ctx: typer.Context, options: _UpdateOptions) -> None:
    app_context = get_app_context(ctx)
    payload = build(
        CommitStatusUpdate,
        options.from_file,
        state=options.state.value if options.state else None,
        url=options.url,
        name=options.name,
        description=options.description,
    )
    status = app_context.repository(options.repo).commit_statuses.update(options.commit, options.status_key, payload)
    app_context.render(single(status, PULL_REQUEST_STATUSES, id_key="key"))


@PROPERTY_APP.command(name="get", help="Print a property value as JSON.")
@handle_errors
def get_property(ctx: typer.Context, commit: CommitHash, app_key: AppKey, name: Name, repo: Repo) -> None:
    app_context = get_app_context(ctx)
    value = app_context.repository(repo).commits.properties(commit).get(app_key, name)
    app_context.write(json.dumps(value))


@PROPERTY_APP.command(name="set", help="Store a property; the value is JSON, or - to read it from stdin.")
@handle_errors
@options_from(_SetOptions)
def set_property(ctx: typer.Context, options: _SetOptions) -> None:
    app_context = get_app_context(ctx)
    parsed = parse_value(options.value)
    app_context.repository(options.repo).commits.properties(options.commit).put(options.app_key, options.name, parsed)
    app_context.notify(f"Stored property '{options.name}'.")


@PROPERTY_APP.command(name="delete", help="Delete a property.")
@handle_errors
def delete_property(ctx: typer.Context, commit: CommitHash, app_key: AppKey, name: Name, repo: Repo) -> None:
    app_context = get_app_context(ctx)
    app_context.repository(repo).commits.properties(commit).delete(app_key, name)
    app_context.notify(f"Deleted property '{name}'.")

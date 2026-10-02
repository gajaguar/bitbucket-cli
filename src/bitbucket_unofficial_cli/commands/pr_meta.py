import json
from dataclasses import dataclass
from typing import Annotated
from typing import Final

import typer

from bitbucket_unofficial_cli.output.columns import PULL_REQUEST_STATUSES
from bitbucket_unofficial_cli.output.renderer import many
from bitbucket_unofficial_cli.runtime.context import get_app_context
from bitbucket_unofficial_cli.runtime.errors import handle_errors
from bitbucket_unofficial_cli.runtime.params import PagingOptions
from bitbucket_unofficial_cli.runtime.params import PullRequestId
from bitbucket_unofficial_cli.runtime.params import Repo
from bitbucket_unofficial_cli.runtime.params import options_from
from bitbucket_unofficial_cli.services.jsonvalue import parse_value
from bitbucket_unofficial_cli.services.listing import paged

STATUS_APP: Final = typer.Typer(help="Build statuses reported on a pull request.", no_args_is_help=True)
PROPERTY_APP: Final = typer.Typer(help="Connect app properties of a pull request.", no_args_is_help=True)

AppKey = Annotated[str, typer.Argument(help="Connect app key.")]  # pylint: disable=gajaguar-module-const-naming,gajaguar-require-final
Name = Annotated[str, typer.Argument(help="Property name.")]  # pylint: disable=gajaguar-module-const-naming,gajaguar-require-final


@dataclass(frozen=True, slots=True, kw_only=True)
class _StatusOptions(PagingOptions):
    repo: Repo
    pr_id: PullRequestId


@STATUS_APP.command(name="list", help="List the build statuses of a pull request.")
@handle_errors
@options_from(_StatusOptions)
def list_statuses(ctx: typer.Context, options: _StatusOptions) -> None:
    app_context = get_app_context(ctx)
    statuses = app_context.repository(options.repo).pull_requests.statuses(options.pr_id)
    found = paged(app_context, options, statuses.list, statuses.list_page)
    app_context.render(many(found, PULL_REQUEST_STATUSES, id_key="key"))


@PROPERTY_APP.command(name="get", help="Print a property value as JSON.")
@handle_errors
def get_property(ctx: typer.Context, pr_id: PullRequestId, app_key: AppKey, name: Name, repo: Repo) -> None:
    app_context = get_app_context(ctx)
    value = app_context.repository(repo).pull_requests.properties(pr_id).get(app_key, name)
    app_context.write(json.dumps(value))


@dataclass(frozen=True, slots=True, kw_only=True)
class _SetOptions:
    repo: Repo
    pr_id: PullRequestId
    app_key: AppKey
    name: Name
    value: Annotated[str, typer.Argument(help="JSON value, or - for stdin.")]


@PROPERTY_APP.command(name="set", help="Store a property; the value is JSON, or - to read it from stdin.")
@handle_errors
@options_from(_SetOptions)
def set_property(ctx: typer.Context, options: _SetOptions) -> None:
    app_context = get_app_context(ctx)
    parsed = parse_value(options.value)
    app_context.repository(options.repo).pull_requests.properties(options.pr_id).put(
        options.app_key, options.name, parsed
    )
    app_context.notify(f"Stored property '{options.name}'.")


@PROPERTY_APP.command(name="delete", help="Delete a property.")
@handle_errors
def delete_property(ctx: typer.Context, pr_id: PullRequestId, app_key: AppKey, name: Name, repo: Repo) -> None:
    app_context = get_app_context(ctx)
    app_context.repository(repo).pull_requests.properties(pr_id).delete(app_key, name)
    app_context.notify(f"Deleted property '{name}'.")

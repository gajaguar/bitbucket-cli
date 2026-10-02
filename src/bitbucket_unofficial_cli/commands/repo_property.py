import json
from dataclasses import dataclass
from typing import Annotated
from typing import Final

import typer

from bitbucket_unofficial_cli.runtime.context import get_app_context
from bitbucket_unofficial_cli.runtime.errors import handle_errors
from bitbucket_unofficial_cli.runtime.params import Repo
from bitbucket_unofficial_cli.runtime.params import options_from
from bitbucket_unofficial_cli.services.jsonvalue import parse_value

APP: Final = typer.Typer(help="Connect app properties of a repository.", no_args_is_help=True)

AppKey = Annotated[str, typer.Argument(help="Connect app key.")]  # pylint: disable=gajaguar-module-const-naming,gajaguar-require-final
Name = Annotated[str, typer.Argument(help="Property name.")]  # pylint: disable=gajaguar-module-const-naming,gajaguar-require-final


@dataclass(frozen=True, slots=True, kw_only=True)
class _SetOptions:
    repo: Repo
    app_key: AppKey
    name: Name
    value: Annotated[str, typer.Argument(help="JSON value, or - for stdin.")]


@APP.command(name="get", help="Print a property value as JSON.")
@handle_errors
def get_property(ctx: typer.Context, app_key: AppKey, name: Name, repo: Repo) -> None:
    app_context = get_app_context(ctx)
    app_context.write(json.dumps(app_context.repository(repo).properties.get(app_key, name)))


@APP.command(name="set", help="Store a property; the value is JSON, or - to read it from stdin.")
@handle_errors
@options_from(_SetOptions)
def set_property(ctx: typer.Context, options: _SetOptions) -> None:
    app_context = get_app_context(ctx)
    app_context.repository(options.repo).properties.put(options.app_key, options.name, parse_value(options.value))
    app_context.notify(f"Stored property '{options.name}'.")


@APP.command(name="delete", help="Delete a property.")
@handle_errors
def delete_property(ctx: typer.Context, app_key: AppKey, name: Name, repo: Repo) -> None:
    app_context = get_app_context(ctx)
    app_context.repository(repo).properties.delete(app_key, name)
    app_context.notify(f"Deleted property '{name}'.")

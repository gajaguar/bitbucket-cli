from dataclasses import dataclass
from typing import Annotated
from typing import Final

import typer
from bitbucket.models.project import ProjectCreate
from bitbucket.models.project import ProjectUpdate

from bitbucket_unofficial_cli.output.columns import PROJECT
from bitbucket_unofficial_cli.output.columns import PROJECTS
from bitbucket_unofficial_cli.output.renderer import many
from bitbucket_unofficial_cli.output.renderer import single
from bitbucket_unofficial_cli.runtime.context import get_app_context
from bitbucket_unofficial_cli.runtime.errors import handle_errors
from bitbucket_unofficial_cli.runtime.params import FromFile
from bitbucket_unofficial_cli.runtime.params import QueryOptions
from bitbucket_unofficial_cli.runtime.params import Yes
from bitbucket_unofficial_cli.runtime.params import options_from
from bitbucket_unofficial_cli.services.listing import filters
from bitbucket_unofficial_cli.services.listing import paged
from bitbucket_unofficial_cli.services.payloads import build

APP: Final = typer.Typer(help="Manage the projects of the selected workspace.", no_args_is_help=True)

Key = Annotated[str, typer.Argument(help="Project key.")]  # pylint: disable=gajaguar-module-const-naming,gajaguar-require-final


@dataclass(frozen=True, slots=True, kw_only=True)
class _WriteOptions:
    name: Annotated[str | None, typer.Option("--name", help="Project name.")] = None
    description: Annotated[str | None, typer.Option("--description", help="Project description.")] = None
    private: Annotated[bool | None, typer.Option("--private/--public", help="Project visibility.")] = None
    from_file: FromFile = None


@dataclass(frozen=True, slots=True, kw_only=True)
class _CreateOptions(_WriteOptions):
    key: Key


@dataclass(frozen=True, slots=True, kw_only=True)
class _UpdateOptions(_WriteOptions):
    key: Key
    new_key: Annotated[str | None, typer.Option("--new-key", help="Rename the project key.")] = None


@APP.command(name="list", help="List the projects of the selected workspace.")
@handle_errors
@options_from(QueryOptions)
def list_projects(ctx: typer.Context, options: QueryOptions) -> None:
    app_context = get_app_context(ctx)
    projects = app_context.workspace().projects
    params = filters(q=options.query, sort=options.sort)
    found = paged(
        app_context,
        options,
        lambda: projects.list(**params),
        lambda **page: projects.list_page(**params, **page),
    )
    app_context.render(many(found, PROJECTS, id_key="key"))


@APP.command(help="Show a project by key.")
@handle_errors
def get(ctx: typer.Context, key: Key) -> None:
    app_context = get_app_context(ctx)
    app_context.render(single(app_context.workspace().projects.get(key), PROJECT, id_key="key"))


@APP.command(help="Create a project.")
@handle_errors
@options_from(_CreateOptions)
def create(ctx: typer.Context, options: _CreateOptions) -> None:
    app_context = get_app_context(ctx)
    payload = build(
        ProjectCreate,
        options.from_file,
        key=options.key,
        name=options.name,
        description=options.description,
        is_private=options.private,
    )
    app_context.render(single(app_context.workspace().projects.create(payload), PROJECT, id_key="key"))


@APP.command(help="Update a project.")
@handle_errors
@options_from(_UpdateOptions)
def update(ctx: typer.Context, options: _UpdateOptions) -> None:
    app_context = get_app_context(ctx)
    payload = build(
        ProjectUpdate,
        options.from_file,
        key=options.new_key,
        name=options.name,
        description=options.description,
        is_private=options.private,
    )
    app_context.render(single(app_context.workspace().projects.update(options.key, payload), PROJECT, id_key="key"))


@APP.command(help="Delete a project. It must hold no repositories.")
@handle_errors
def delete(ctx: typer.Context, key: Key, *, yes: Yes = False) -> None:
    app_context = get_app_context(ctx)
    app_context.confirm(f"Delete project '{key}'?", assume_yes=yes)
    app_context.workspace().projects.delete(key)
    app_context.notify(f"Deleted project '{key}'.")

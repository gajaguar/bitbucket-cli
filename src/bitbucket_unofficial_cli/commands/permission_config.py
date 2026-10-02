from dataclasses import dataclass
from typing import Annotated
from typing import Any
from typing import Final

import typer
from bitbucket import ProjectClient
from bitbucket.models.permission import GroupPermissionUpdate
from bitbucket.models.permission import PermissionLevel
from bitbucket.models.permission import ProjectPermissionLevel
from bitbucket.models.permission import ProjectPermissionUpdate
from bitbucket.models.permission import RepositoryOverrideSettings
from bitbucket.models.permission import UserPermissionUpdate
from bitbucket.resources.permissions import GroupPermissionsBase
from bitbucket.resources.permissions import UserPermissionsBase

from bitbucket_unofficial_cli.output.columns import GROUP_PERMISSIONS
from bitbucket_unofficial_cli.output.columns import OVERRIDE_SETTINGS
from bitbucket_unofficial_cli.output.columns import USER_PERMISSIONS
from bitbucket_unofficial_cli.output.renderer import many
from bitbucket_unofficial_cli.output.renderer import single
from bitbucket_unofficial_cli.runtime.context import get_app_context
from bitbucket_unofficial_cli.runtime.errors import handle_errors
from bitbucket_unofficial_cli.runtime.params import OptionalRepo
from bitbucket_unofficial_cli.runtime.params import PagingOptions
from bitbucket_unofficial_cli.runtime.params import ProjectScope
from bitbucket_unofficial_cli.runtime.params import Repo
from bitbucket_unofficial_cli.runtime.params import one_of
from bitbucket_unofficial_cli.runtime.params import options_from
from bitbucket_unofficial_cli.runtime.scope import resolve_scope
from bitbucket_unofficial_cli.services.listing import paged
from bitbucket_unofficial_cli.services.payloads import build
from bitbucket_unofficial_cli.services.payloads import check_choice

APP: Final = typer.Typer(help="Manage explicit repository and project permissions.", no_args_is_help=True)
GROUP_APP: Final = typer.Typer(help="Group permissions.", no_args_is_help=True)
USER_APP: Final = typer.Typer(help="User permissions.", no_args_is_help=True)
OVERRIDE_APP: Final = typer.Typer(help="Whether a repository overrides its project's settings.", no_args_is_help=True)
APP.add_typer(GROUP_APP, name="group")
APP.add_typer(USER_APP, name="user")
APP.add_typer(OVERRIDE_APP, name="override")

Slug = Annotated[str, typer.Argument(help="Group slug.")]  # pylint: disable=gajaguar-module-const-naming,gajaguar-require-final
Account = Annotated[str, typer.Argument(help="User account ID.")]  # pylint: disable=gajaguar-module-const-naming,gajaguar-require-final
_LEVELS: Final = f"{one_of(PermissionLevel)} Projects also take create-repo."


@dataclass(frozen=True, slots=True, kw_only=True)
class _ListOptions(PagingOptions):
    repo: OptionalRepo = None
    project: ProjectScope = None


@dataclass(frozen=True, slots=True, kw_only=True)
class _GroupOptions:
    slug: Slug
    repo: OptionalRepo = None
    project: ProjectScope = None


@dataclass(frozen=True, slots=True, kw_only=True)
class _UserOptions:
    account: Account
    repo: OptionalRepo = None
    project: ProjectScope = None


@dataclass(frozen=True, slots=True, kw_only=True)
class _SetGroupOptions(_GroupOptions):
    permission: Annotated[str, typer.Option("--permission", help=_LEVELS)]


@dataclass(frozen=True, slots=True, kw_only=True)
class _SetUserOptions(_UserOptions):
    permission: Annotated[str, typer.Option("--permission", help=_LEVELS)]


@dataclass(frozen=True, slots=True, kw_only=True)
class _DeleteGroupOptions(_GroupOptions):
    yes: Annotated[bool, typer.Option("--yes", "-y", help="Do not ask for confirmation.")] = False


@dataclass(frozen=True, slots=True, kw_only=True)
class _DeleteUserOptions(_UserOptions):
    yes: Annotated[bool, typer.Option("--yes", "-y", help="Do not ask for confirmation.")] = False


@dataclass(frozen=True, slots=True, kw_only=True)
class _OverrideSetOptions:
    repo: Repo
    branching_model: Annotated[
        bool | None, typer.Option("--branching-model/--inherit-branching-model", help="Override the branching model.")
    ] = None
    branch_restrictions: Annotated[
        bool | None,
        typer.Option("--branch-restrictions/--inherit-branch-restrictions", help="Override branch restrictions."),
    ] = None
    default_merge_strategy: Annotated[
        bool | None,
        typer.Option("--merge-strategy/--inherit-merge-strategy", help="Override the default merge strategy."),
    ] = None


def _groups(client: object) -> GroupPermissionsBase[Any, Any]:
    return client.permissions.groups  # type: ignore[attr-defined, no-any-return]


def _users(client: object) -> UserPermissionsBase[Any, Any]:
    return client.permissions.users  # type: ignore[attr-defined, no-any-return]


def _level(client: object, permission: str) -> str | None:
    levels = ProjectPermissionLevel if isinstance(client, ProjectClient) else PermissionLevel
    return check_choice(permission, levels, "--permission")


@GROUP_APP.command(name="list", help="List explicit group permissions.")
@handle_errors
@options_from(_ListOptions)
def list_groups(ctx: typer.Context, options: _ListOptions) -> None:
    app_context = get_app_context(ctx)
    groups = _groups(resolve_scope(ctx, app_context, options.repo, options.project))
    found = paged(app_context, options, groups.list, groups.list_page)
    app_context.render(many(found, GROUP_PERMISSIONS, id_key="group.slug"))


@GROUP_APP.command(name="get", help="Show a group's permission.")
@handle_errors
@options_from(_GroupOptions)
def get_group(ctx: typer.Context, options: _GroupOptions) -> None:
    app_context = get_app_context(ctx)
    groups = _groups(resolve_scope(ctx, app_context, options.repo, options.project))
    app_context.render(single(groups.get(options.slug), GROUP_PERMISSIONS, id_key="group.slug"))


@GROUP_APP.command(name="set", help="Grant a group a permission.")
@handle_errors
@options_from(_SetGroupOptions)
def set_group(ctx: typer.Context, options: _SetGroupOptions) -> None:
    app_context = get_app_context(ctx)
    client = resolve_scope(ctx, app_context, options.repo, options.project)
    level = _level(client, options.permission)
    model = ProjectPermissionUpdate if isinstance(client, ProjectClient) else GroupPermissionUpdate
    updated = _groups(client).update(options.slug, build(model, permission=level))
    app_context.render(single(updated, GROUP_PERMISSIONS, id_key="group.slug"))


@GROUP_APP.command(name="delete", help="Remove a group's explicit permission.")
@handle_errors
@options_from(_DeleteGroupOptions)
def delete_group(ctx: typer.Context, options: _DeleteGroupOptions) -> None:
    app_context = get_app_context(ctx)
    groups = _groups(resolve_scope(ctx, app_context, options.repo, options.project))
    app_context.confirm(f"Remove the permission of group '{options.slug}'?", assume_yes=options.yes)
    groups.delete(options.slug)
    app_context.notify(f"Removed the permission of group '{options.slug}'.")


@USER_APP.command(name="list", help="List explicit user permissions.")
@handle_errors
@options_from(_ListOptions)
def list_users(ctx: typer.Context, options: _ListOptions) -> None:
    app_context = get_app_context(ctx)
    users = _users(resolve_scope(ctx, app_context, options.repo, options.project))
    found = paged(app_context, options, users.list, users.list_page)
    app_context.render(many(found, USER_PERMISSIONS, id_key="user.account_id"))


@USER_APP.command(name="get", help="Show a user's permission.")
@handle_errors
@options_from(_UserOptions)
def get_user(ctx: typer.Context, options: _UserOptions) -> None:
    app_context = get_app_context(ctx)
    users = _users(resolve_scope(ctx, app_context, options.repo, options.project))
    app_context.render(single(users.get(options.account), USER_PERMISSIONS, id_key="user.account_id"))


@USER_APP.command(name="set", help="Grant a user a permission.")
@handle_errors
@options_from(_SetUserOptions)
def set_user(ctx: typer.Context, options: _SetUserOptions) -> None:
    app_context = get_app_context(ctx)
    client = resolve_scope(ctx, app_context, options.repo, options.project)
    level = _level(client, options.permission)
    model = ProjectPermissionUpdate if isinstance(client, ProjectClient) else UserPermissionUpdate
    updated = _users(client).update(options.account, build(model, permission=level))
    app_context.render(single(updated, USER_PERMISSIONS, id_key="user.account_id"))


@USER_APP.command(name="delete", help="Remove a user's explicit permission.")
@handle_errors
@options_from(_DeleteUserOptions)
def delete_user(ctx: typer.Context, options: _DeleteUserOptions) -> None:
    app_context = get_app_context(ctx)
    users = _users(resolve_scope(ctx, app_context, options.repo, options.project))
    app_context.confirm(f"Remove the permission of user '{options.account}'?", assume_yes=options.yes)
    users.delete(options.account)
    app_context.notify(f"Removed the permission of user '{options.account}'.")


@OVERRIDE_APP.command(name="show", help="Show which project settings a repository overrides.")
@handle_errors
def show_override(ctx: typer.Context, repo: Repo) -> None:
    app_context = get_app_context(ctx)
    state = app_context.repository(repo).permissions.override_settings()
    app_context.render(single(state, OVERRIDE_SETTINGS, id_key="type"))


@OVERRIDE_APP.command(name="set", help="Choose which project settings a repository overrides.")
@handle_errors
@options_from(_OverrideSetOptions)
def set_override(ctx: typer.Context, options: _OverrideSetOptions) -> None:
    app_context = get_app_context(ctx)
    payload = build(
        RepositoryOverrideSettings,
        branching_model=options.branching_model,
        branch_restrictions=options.branch_restrictions,
        default_merge_strategy=options.default_merge_strategy,
    )
    permissions = app_context.repository(options.repo).permissions
    permissions.update_override_settings(payload)
    app_context.render(single(permissions.override_settings(), OVERRIDE_SETTINGS, id_key="type"))

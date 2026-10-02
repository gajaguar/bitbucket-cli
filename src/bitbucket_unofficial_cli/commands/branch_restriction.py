from dataclasses import dataclass
from typing import Annotated
from typing import Final

import typer
from bitbucket.models.branch_restriction import BranchMatchKind
from bitbucket.models.branch_restriction import BranchRestrictionCreate
from bitbucket.models.branch_restriction import BranchRestrictionKind
from bitbucket.models.branch_restriction import BranchRestrictionUpdate
from bitbucket.models.branch_restriction import BranchType

from bitbucket_unofficial_cli.output.columns import BRANCH_RESTRICTIONS
from bitbucket_unofficial_cli.output.renderer import many
from bitbucket_unofficial_cli.output.renderer import single
from bitbucket_unofficial_cli.runtime.context import get_app_context
from bitbucket_unofficial_cli.runtime.errors import handle_errors
from bitbucket_unofficial_cli.runtime.params import FromFile
from bitbucket_unofficial_cli.runtime.params import QueryOptions
from bitbucket_unofficial_cli.runtime.params import Repo
from bitbucket_unofficial_cli.runtime.params import Yes
from bitbucket_unofficial_cli.runtime.params import one_of
from bitbucket_unofficial_cli.runtime.params import options_from
from bitbucket_unofficial_cli.services.listing import filters
from bitbucket_unofficial_cli.services.listing import paged
from bitbucket_unofficial_cli.services.payloads import build
from bitbucket_unofficial_cli.services.payloads import check_choice

APP: Final = typer.Typer(help="Manage the branch restrictions of a repository.", no_args_is_help=True)

RestrictionId = Annotated[int, typer.Argument(help="Branch restriction ID.")]  # pylint: disable=gajaguar-module-const-naming,gajaguar-require-final


@dataclass(frozen=True, slots=True, kw_only=True)
class _ListOptions(QueryOptions):
    repo: Repo
    kind: Annotated[str | None, typer.Option("--kind", help="Only this kind. " + one_of(BranchRestrictionKind))] = None
    pattern: Annotated[str | None, typer.Option("--pattern", help="Only this branch pattern.")] = None


@dataclass(frozen=True, slots=True, kw_only=True)
class _WriteOptions:
    repo: Repo
    kind: Annotated[str | None, typer.Option("--kind", help="Restriction kind. " + one_of(BranchRestrictionKind))] = (
        None
    )
    match_kind: Annotated[
        str | None, typer.Option("--match", help="How branches match. " + one_of(BranchMatchKind))
    ] = None
    branch_type: Annotated[
        str | None, typer.Option("--branch-type", help="Branching model type. " + one_of(BranchType))
    ] = None
    pattern: Annotated[str | None, typer.Option("--pattern", help="Glob pattern, e.g. 'release/*'.")] = None
    value: Annotated[int | None, typer.Option("--value", help="Number, for kinds that take one.")] = None
    users: Annotated[list[str] | None, typer.Option("--user", help="Exempt user UUID; repeatable.")] = None
    groups: Annotated[list[str] | None, typer.Option("--group", help="Exempt group slug; repeatable.")] = None
    from_file: FromFile = None


@dataclass(frozen=True, slots=True, kw_only=True)
class _UpdateOptions(_WriteOptions):
    restriction_id: RestrictionId


def _fields(options: _WriteOptions) -> dict[str, object]:
    return {
        "kind": check_choice(options.kind, BranchRestrictionKind, "--kind"),
        "branch_match_kind": check_choice(options.match_kind, BranchMatchKind, "--match"),
        "branch_type": check_choice(options.branch_type, BranchType, "--branch-type"),
        "pattern": options.pattern,
        "value": options.value,
        "users": [{"uuid": uuid} for uuid in options.users] if options.users else None,
        "groups": [{"slug": slug} for slug in options.groups] if options.groups else None,
    }


@APP.command(name="list", help="List the branch restrictions of a repository.")
@handle_errors
@options_from(_ListOptions)
def list_restrictions(ctx: typer.Context, options: _ListOptions) -> None:
    app_context = get_app_context(ctx)
    restrictions = app_context.repository(options.repo).branch_restrictions
    params = filters(q=options.query, sort=options.sort, kind=options.kind, pattern=options.pattern)
    found = paged(
        app_context,
        options,
        lambda: restrictions.list(**params),
        lambda **page: restrictions.list_page(**params, **page),
    )
    app_context.render(many(found, BRANCH_RESTRICTIONS, id_key="id"))


@APP.command(help="Show a branch restriction.")
@handle_errors
def get(ctx: typer.Context, restriction_id: RestrictionId, repo: Repo) -> None:
    app_context = get_app_context(ctx)
    restriction = app_context.repository(repo).branch_restrictions.get(restriction_id)
    app_context.render(single(restriction, BRANCH_RESTRICTIONS, id_key="id"))


@APP.command(help="Add a branch restriction.")
@handle_errors
@options_from(_WriteOptions)
def create(ctx: typer.Context, options: _WriteOptions) -> None:
    app_context = get_app_context(ctx)
    payload = build(BranchRestrictionCreate, options.from_file, **_fields(options))
    created = app_context.repository(options.repo).branch_restrictions.create(payload)
    app_context.render(single(created, BRANCH_RESTRICTIONS, id_key="id"))


@APP.command(help="Change a branch restriction.")
@handle_errors
@options_from(_UpdateOptions)
def update(ctx: typer.Context, options: _UpdateOptions) -> None:
    app_context = get_app_context(ctx)
    payload = build(BranchRestrictionUpdate, options.from_file, **_fields(options))
    restrictions = app_context.repository(options.repo).branch_restrictions
    app_context.render(single(restrictions.update(options.restriction_id, payload), BRANCH_RESTRICTIONS, id_key="id"))


@APP.command(help="Delete a branch restriction.")
@handle_errors
def delete(ctx: typer.Context, restriction_id: RestrictionId, repo: Repo, *, yes: Yes = False) -> None:
    app_context = get_app_context(ctx)
    app_context.confirm(f"Delete branch restriction {restriction_id}?", assume_yes=yes)
    app_context.repository(repo).branch_restrictions.delete(restriction_id)
    app_context.notify(f"Deleted branch restriction {restriction_id}.")

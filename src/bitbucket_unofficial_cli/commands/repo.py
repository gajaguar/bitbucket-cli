from dataclasses import dataclass
from enum import StrEnum
from typing import Annotated
from typing import Final

import typer
from bitbucket.models.repository import ForkCreate
from bitbucket.models.repository import RepositoryCreate
from bitbucket.models.repository import RepositoryUpdate

from bitbucket_unofficial_cli.commands import repo_property
from bitbucket_unofficial_cli.output.columns import ACCOUNTS
from bitbucket_unofficial_cli.output.columns import REPOSITORIES
from bitbucket_unofficial_cli.output.columns import REPOSITORY
from bitbucket_unofficial_cli.output.renderer import many
from bitbucket_unofficial_cli.output.renderer import single
from bitbucket_unofficial_cli.runtime.context import get_app_context
from bitbucket_unofficial_cli.runtime.errors import handle_errors
from bitbucket_unofficial_cli.runtime.params import FromFile
from bitbucket_unofficial_cli.runtime.params import PagingOptions
from bitbucket_unofficial_cli.runtime.params import QueryOptions
from bitbucket_unofficial_cli.runtime.params import Yes
from bitbucket_unofficial_cli.runtime.params import options_from
from bitbucket_unofficial_cli.services.listing import paged
from bitbucket_unofficial_cli.services.payloads import build

APP: Final = typer.Typer(help="Manage repositories in the selected workspace.", no_args_is_help=True)
APP.add_typer(repo_property.APP, name="property")

Slug = Annotated[str, typer.Argument(help="Repository slug.")]  # pylint: disable=gajaguar-module-const-naming,gajaguar-require-final


class _ForkPolicy(StrEnum):
    ALLOW_FORKS = "allow_forks"
    NO_PUBLIC_FORKS = "no_public_forks"
    NO_FORKS = "no_forks"


@dataclass(frozen=True, slots=True, kw_only=True)
class _WriteOptions:
    description: Annotated[str | None, typer.Option("--description", help="Repository description.")] = None
    private: Annotated[bool | None, typer.Option("--private/--public", help="Repository visibility.")] = None
    project: Annotated[str | None, typer.Option("--project", help="Key of the project that holds it.")] = None
    fork_policy: Annotated[_ForkPolicy | None, typer.Option("--fork-policy", help="Who may fork it.")] = None
    language: Annotated[str | None, typer.Option("--language", help="Primary language.")] = None
    issues: Annotated[bool | None, typer.Option("--issues/--no-issues", help="Enable the issue tracker.")] = None
    wiki: Annotated[bool | None, typer.Option("--wiki/--no-wiki", help="Enable the wiki.")] = None
    from_file: FromFile = None


@dataclass(frozen=True, slots=True, kw_only=True)
class _CreateOptions(_WriteOptions):
    slug: Slug


@dataclass(frozen=True, slots=True, kw_only=True)
class _UpdateOptions(_WriteOptions):
    slug: Slug


@dataclass(frozen=True, slots=True, kw_only=True)
class _SlugPaging(PagingOptions):
    slug: Slug


def _fields(options: _WriteOptions) -> dict[str, object]:
    return {
        "description": options.description,
        "is_private": options.private,
        "project": {"key": options.project} if options.project else None,
        "fork_policy": options.fork_policy.value if options.fork_policy else None,
        "language": options.language,
        "has_issues": options.issues,
        "has_wiki": options.wiki,
    }


@APP.command(name="list", help="List the repositories of the selected workspace.")
@handle_errors
@options_from(QueryOptions)
def list_repositories(ctx: typer.Context, options: QueryOptions) -> None:
    app_context = get_app_context(ctx)
    repositories = app_context.workspace().repositories
    found = paged(
        app_context,
        options,
        lambda: repositories.list(q=options.query, sort=options.sort),
        lambda **page: repositories.list_page(q=options.query, sort=options.sort, **page),
    )
    app_context.render(many(found, REPOSITORIES, id_key="slug"))


@APP.command(help="Show a repository by slug.")
@handle_errors
def get(ctx: typer.Context, slug: Slug) -> None:
    app_context = get_app_context(ctx)
    repository = app_context.workspace().repositories.get(slug)
    app_context.render(single(repository, REPOSITORY, id_key="slug"))


@APP.command(help="Create a repository.")
@handle_errors
@options_from(_CreateOptions)
def create(ctx: typer.Context, options: _CreateOptions) -> None:
    app_context = get_app_context(ctx)
    payload = build(RepositoryCreate, options.from_file, **_fields(options))
    created = app_context.workspace().repositories.create(options.slug, payload)
    app_context.render(single(created, REPOSITORY, id_key="slug"))


@APP.command(help="Update a repository.")
@handle_errors
@options_from(_UpdateOptions)
def update(ctx: typer.Context, options: _UpdateOptions) -> None:
    app_context = get_app_context(ctx)
    payload = build(RepositoryUpdate, options.from_file, **_fields(options))
    updated = app_context.workspace().repositories.update(options.slug, payload)
    app_context.render(single(updated, REPOSITORY, id_key="slug"))


@APP.command(help="Delete a repository. This cannot be undone.")
@handle_errors
def delete(ctx: typer.Context, slug: Slug, *, yes: Yes = False) -> None:
    app_context = get_app_context(ctx)
    app_context.confirm(f"Delete repository '{slug}'?", assume_yes=yes)
    app_context.workspace().repositories.delete(slug)
    app_context.notify(f"Deleted repository '{slug}'.")


@APP.command(help="Fork a repository.")
@handle_errors
def fork(
    ctx: typer.Context,
    slug: Slug,
    name: Annotated[str | None, typer.Option("--name", help="Name of the fork.")] = None,
    to_workspace: Annotated[str | None, typer.Option("--to-workspace", help="Workspace for the fork.")] = None,
    private: Annotated[bool | None, typer.Option("--private/--public", help="Visibility of the fork.")] = None,
) -> None:
    app_context = get_app_context(ctx)
    payload = build(
        ForkCreate,
        name=name,
        workspace={"slug": to_workspace} if to_workspace else None,
        is_private=private,
    )
    forked = app_context.workspace().repositories.create_fork(slug, payload)
    app_context.render(single(forked, REPOSITORY, id_key="slug"))


@APP.command(help="List the forks of a repository.")
@handle_errors
@options_from(_SlugPaging)
def forks(ctx: typer.Context, options: _SlugPaging) -> None:
    app_context = get_app_context(ctx)
    slug = options.slug
    repositories = app_context.workspace().repositories
    found = paged(
        app_context,
        options,
        lambda: repositories.forks(slug),
        lambda **page: repositories.forks_page(slug, **page),
    )
    app_context.render(many(found, REPOSITORIES, id_key="slug"))


@APP.command(help="List the watchers of a repository.")
@handle_errors
@options_from(_SlugPaging)
def watchers(ctx: typer.Context, options: _SlugPaging) -> None:
    app_context = get_app_context(ctx)
    slug = options.slug
    repositories = app_context.workspace().repositories
    found = paged(
        app_context,
        options,
        lambda: repositories.watchers(slug),
        lambda **page: repositories.watchers_page(slug, **page),
    )
    app_context.render(many(found, ACCOUNTS, id_key="account_id"))

from dataclasses import dataclass
from typing import Annotated
from typing import Final

import typer

from bitbucket_unofficial_cli.commands import commit_comment
from bitbucket_unofficial_cli.commands import commit_meta
from bitbucket_unofficial_cli.output.columns import ACCOUNTS
from bitbucket_unofficial_cli.output.columns import COMMIT
from bitbucket_unofficial_cli.output.columns import COMMITS
from bitbucket_unofficial_cli.output.columns import CONFLICTS
from bitbucket_unofficial_cli.output.columns import DIFFSTATS
from bitbucket_unofficial_cli.output.columns import PULL_REQUESTS
from bitbucket_unofficial_cli.output.renderer import many
from bitbucket_unofficial_cli.output.renderer import single
from bitbucket_unofficial_cli.runtime.context import get_app_context
from bitbucket_unofficial_cli.runtime.errors import handle_errors
from bitbucket_unofficial_cli.runtime.params import PagingOptions
from bitbucket_unofficial_cli.runtime.params import Repo
from bitbucket_unofficial_cli.runtime.params import options_from
from bitbucket_unofficial_cli.services.listing import paged

APP: Final = typer.Typer(help="Work with the commits of a repository.", no_args_is_help=True)
APP.add_typer(commit_comment.APP, name="comment")
APP.add_typer(commit_meta.STATUS_APP, name="status")
APP.add_typer(commit_meta.PROPERTY_APP, name="property")

Hash = Annotated[str, typer.Argument(help="Commit hash.")]  # pylint: disable=gajaguar-module-const-naming,gajaguar-require-final
Spec = Annotated[str, typer.Argument(help="Revspec: a commit, or A..B for a range.")]  # pylint: disable=gajaguar-module-const-naming,gajaguar-require-final


@dataclass(frozen=True, slots=True, kw_only=True)
class _PrsOptions(PagingOptions):
    repo: Repo
    commit: Hash


@dataclass(frozen=True, slots=True, kw_only=True)
class _ListOptions(PagingOptions):
    repo: Repo
    revision: Annotated[str | None, typer.Option("--revision", help="List the commits reachable from this one.")] = (
        None
    )
    include: Annotated[
        list[str] | None, typer.Option("--include", help="Include commits reachable from; repeatable.")
    ] = None
    exclude: Annotated[
        list[str] | None, typer.Option("--exclude", help="Exclude commits reachable from; repeatable.")
    ] = None
    post: Annotated[bool, typer.Option("--post", help="Send the filters in a POST body, for long lists.")] = False


@dataclass(frozen=True, slots=True, kw_only=True)
class _SpecOptions(PagingOptions):
    repo: Repo
    spec: Spec


@APP.command(help="List the pull requests that contain a commit.")
@handle_errors
@options_from(_PrsOptions)
def prs(ctx: typer.Context, options: _PrsOptions) -> None:
    app_context = get_app_context(ctx)
    repositories = app_context.workspace().repositories
    found = paged(
        app_context,
        options,
        lambda: repositories.commit_pull_requests(options.repo, options.commit),
        lambda **page: repositories.commit_pull_requests_page(options.repo, options.commit, **page),
    )
    app_context.render(many(found, PULL_REQUESTS, id_key="id"))


@APP.command(name="list", help="List commits, newest first.")
@handle_errors
@options_from(_ListOptions)
def list_commits(ctx: typer.Context, options: _ListOptions) -> None:
    app_context = get_app_context(ctx)
    commits = app_context.repository(options.repo).commits
    include, exclude, revision = options.include or [], options.exclude or [], options.revision
    if options.post or len(include) > 1 or len(exclude) > 1:
        if revision:
            found = paged(
                app_context,
                options,
                lambda: commits.list_from_by_post(revision, include=include, exclude=exclude),
                lambda **page: commits.list_from_by_post_page(revision, include=include, exclude=exclude, **page),
            )
        else:
            found = paged(
                app_context,
                options,
                lambda: commits.list_by_post(include=include, exclude=exclude),
                lambda **page: commits.list_by_post_page(include=include, exclude=exclude, **page),
            )
    elif revision:
        found = paged(
            app_context,
            options,
            lambda: commits.list_from(revision),
            lambda **page: commits.list_from_page(revision, **page),
        )
    else:
        one_include = include[0] if include else None
        one_exclude = exclude[0] if exclude else None
        found = paged(
            app_context,
            options,
            lambda: commits.list(include=one_include, exclude=one_exclude),
            lambda **page: commits.list_page(include=one_include, exclude=one_exclude, **page),
        )
    app_context.render(many(found, COMMITS, id_key="hash"))


@APP.command(help="Show a commit.")
@handle_errors
def get(ctx: typer.Context, commit: Hash, repo: Repo) -> None:
    app_context = get_app_context(ctx)
    app_context.render(single(app_context.repository(repo).commits.get(commit), COMMIT, id_key="hash"))


@APP.command(name="merge-base", help="Show the best common ancestor of two commits.")
@handle_errors
def merge_base(ctx: typer.Context, spec: Annotated[str, typer.Argument(help="A..B")], repo: Repo) -> None:
    app_context = get_app_context(ctx)
    app_context.render(single(app_context.repository(repo).commits.merge_base(spec), COMMIT, id_key="hash"))


@APP.command(help="Approve a commit.")
@handle_errors
def approve(ctx: typer.Context, commit: Hash, repo: Repo) -> None:
    app_context = get_app_context(ctx)
    account = app_context.repository(repo).commits.approve(commit)
    app_context.render(single(account, ACCOUNTS, id_key="account_id"))


@APP.command(help="Withdraw your approval of a commit.")
@handle_errors
def unapprove(ctx: typer.Context, commit: Hash, repo: Repo) -> None:
    app_context = get_app_context(ctx)
    app_context.repository(repo).commits.unapprove(commit)
    app_context.notify(f"Withdrew approval of {commit}.")


@APP.command(help="Print the diff of a commit or range.")
@handle_errors
def diff(ctx: typer.Context, spec: Spec, repo: Repo) -> None:
    app_context = get_app_context(ctx)
    app_context.write(app_context.repository(repo).commits.diff(spec))


@APP.command(help="Print the patch of a commit or range.")
@handle_errors
def patch(ctx: typer.Context, spec: Spec, repo: Repo) -> None:
    app_context = get_app_context(ctx)
    app_context.write(app_context.repository(repo).commits.patch(spec))


@APP.command(help="List the files a commit or range changes.")
@handle_errors
@options_from(_SpecOptions)
def diffstat(ctx: typer.Context, options: _SpecOptions) -> None:
    app_context = get_app_context(ctx)
    commits = app_context.repository(options.repo).commits
    found = paged(
        app_context,
        options,
        lambda: commits.diffstat(options.spec),
        lambda **page: commits.diffstat_page(options.spec, **page),
    )
    app_context.render(many(found, DIFFSTATS, id_key="new.path"))


@APP.command(help="List the files that would conflict when merging A..B.")
@handle_errors
@options_from(_SpecOptions)
def conflicts(ctx: typer.Context, options: _SpecOptions) -> None:
    app_context = get_app_context(ctx)
    commits = app_context.repository(options.repo).commits
    found = paged(
        app_context,
        options,
        lambda: commits.file_conflicts(options.spec),
        lambda **page: commits.file_conflicts_page(options.spec, **page),
    )
    app_context.render(many(found, CONFLICTS, id_key="path"))

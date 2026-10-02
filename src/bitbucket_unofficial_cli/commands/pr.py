from dataclasses import dataclass
from enum import StrEnum
from typing import Annotated
from typing import Final

import typer
from bitbucket.models.merge import MergeParameters
from bitbucket.models.pull_request import PullRequestCreate
from bitbucket.models.pull_request import PullRequestUpdate

from bitbucket_unofficial_cli.commands import pr_comment
from bitbucket_unofficial_cli.commands import pr_meta
from bitbucket_unofficial_cli.commands import pr_task
from bitbucket_unofficial_cli.output.columns import ACCOUNTS
from bitbucket_unofficial_cli.output.columns import ACTIVITIES
from bitbucket_unofficial_cli.output.columns import CHECKS
from bitbucket_unofficial_cli.output.columns import COMMITS
from bitbucket_unofficial_cli.output.columns import CONFLICTS
from bitbucket_unofficial_cli.output.columns import DIFFSTATS
from bitbucket_unofficial_cli.output.columns import MERGE_STATUS
from bitbucket_unofficial_cli.output.columns import MERGE_TASK
from bitbucket_unofficial_cli.output.columns import PULL_REQUEST
from bitbucket_unofficial_cli.output.columns import PULL_REQUESTS
from bitbucket_unofficial_cli.output.renderer import many
from bitbucket_unofficial_cli.output.renderer import single
from bitbucket_unofficial_cli.runtime.context import get_app_context
from bitbucket_unofficial_cli.runtime.errors import handle_errors
from bitbucket_unofficial_cli.runtime.params import FromFile
from bitbucket_unofficial_cli.runtime.params import PagingOptions
from bitbucket_unofficial_cli.runtime.params import PullRequestId
from bitbucket_unofficial_cli.runtime.params import QueryOptions
from bitbucket_unofficial_cli.runtime.params import Repo
from bitbucket_unofficial_cli.runtime.params import options_from
from bitbucket_unofficial_cli.services.listing import filters
from bitbucket_unofficial_cli.services.listing import paged
from bitbucket_unofficial_cli.services.payloads import build

APP: Final = typer.Typer(help="Work with pull requests of a repository.", no_args_is_help=True)
APP.add_typer(pr_comment.APP, name="comment")
APP.add_typer(pr_task.APP, name="task")
APP.add_typer(pr_meta.STATUS_APP, name="status")
APP.add_typer(pr_meta.PROPERTY_APP, name="property")


class _State(StrEnum):
    OPEN = "OPEN"
    DRAFT = "DRAFT"
    QUEUED = "QUEUED"
    MERGED = "MERGED"
    DECLINED = "DECLINED"
    SUPERSEDED = "SUPERSEDED"


class _Strategy(StrEnum):
    MERGE_COMMIT = "merge_commit"
    SQUASH = "squash"
    FAST_FORWARD = "fast_forward"


_StateOption = Annotated[  # pylint: disable=gajaguar-module-const-naming,gajaguar-require-final
    list[_State] | None,
    typer.Option("--state", help="Only pull requests in this state; repeatable."),
]


@dataclass(frozen=True, slots=True, kw_only=True)
class _ListOptions(QueryOptions):
    repo: Repo
    state: _StateOption = None


@dataclass(frozen=True, slots=True, kw_only=True)
class _ByAuthorOptions(PagingOptions):
    user: Annotated[str, typer.Argument(help="Author's account ID or UUID.")]
    state: _StateOption = None


@dataclass(frozen=True, slots=True, kw_only=True)
class _CreateOptions:
    repo: Repo
    title: Annotated[str | None, typer.Option("--title", help="Pull request title.")] = None
    source: Annotated[str | None, typer.Option("--source", help="Source branch.")] = None
    destination: Annotated[str | None, typer.Option("--destination", help="Destination branch.")] = None
    description: Annotated[str | None, typer.Option("--description", help="Pull request description.")] = None
    reviewers: Annotated[list[str] | None, typer.Option("--reviewer", help="Reviewer UUID; repeatable.")] = None
    close_source_branch: Annotated[
        bool | None,
        typer.Option("--close-source-branch/--keep-source-branch", help="Close the source branch on merge."),
    ] = None
    from_file: FromFile = None


@dataclass(frozen=True, slots=True, kw_only=True)
class _UpdateOptions:
    repo: Repo
    pr_id: PullRequestId
    title: Annotated[str | None, typer.Option("--title", help="Pull request title.")] = None
    destination: Annotated[str | None, typer.Option("--destination", help="Destination branch.")] = None
    description: Annotated[str | None, typer.Option("--description", help="Pull request description.")] = None
    reviewers: Annotated[list[str] | None, typer.Option("--reviewer", help="Reviewer UUID; repeatable.")] = None
    from_file: FromFile = None


@dataclass(frozen=True, slots=True, kw_only=True)
class _MergeOptions:
    repo: Repo
    pr_id: PullRequestId
    message: Annotated[str | None, typer.Option("--message", "-m", help="Merge commit message.")] = None
    strategy: Annotated[_Strategy | None, typer.Option("--strategy", help="Merge strategy.")] = None
    close_source_branch: Annotated[
        bool | None,
        typer.Option("--close-source-branch/--keep-source-branch", help="Close the source branch."),
    ] = None
    wait: Annotated[bool, typer.Option("--wait", help="Wait until the merge finishes.")] = False
    timeout: Annotated[float, typer.Option("--timeout", help="Seconds to wait with --wait.")] = 60.0


@dataclass(frozen=True, slots=True, kw_only=True)
class _PagedPullRequest(PagingOptions):
    repo: Repo
    pr_id: PullRequestId


@dataclass(frozen=True, slots=True, kw_only=True)
class _ActivityOptions(PagingOptions):
    repo: Repo
    pr_id: Annotated[int | None, typer.Argument(help="Pull request ID; omit for the whole repository.")] = None


@dataclass(frozen=True, slots=True, kw_only=True)
class _ChecksOptions:
    repo: Repo
    pr_id: PullRequestId
    query: Annotated[str | None, typer.Option("--query", "-q", help="Bitbucket query filter.")] = None


def _states(values: list[_State] | None) -> list[str] | None:
    return [state.value for state in values] if values else None


@APP.command(name="list", help="List the pull requests of a repository.")
@handle_errors
@options_from(_ListOptions)
def list_pull_requests(ctx: typer.Context, options: _ListOptions) -> None:
    app_context = get_app_context(ctx)
    requests = app_context.repository(options.repo).pull_requests
    params = filters(q=options.query, sort=options.sort, state=_states(options.state))
    found = paged(
        app_context,
        options,
        lambda: requests.list(**params),
        lambda **page: requests.list_page(**params, **page),
    )
    app_context.render(many(found, PULL_REQUESTS, id_key="id"))


@APP.command(name="by-author", help="List the pull requests a user authored in the workspace.")
@handle_errors
@options_from(_ByAuthorOptions)
def by_author(ctx: typer.Context, options: _ByAuthorOptions) -> None:
    app_context = get_app_context(ctx)
    workspace = app_context.workspace()
    states = [state.value for state in options.state] if options.state else None
    found = paged(
        app_context,
        options,
        lambda: workspace.pull_requests_by_author(options.user, states=states),  # type: ignore[arg-type]
        lambda **page: workspace.pull_requests_by_author_page(options.user, states=states, **page),  # type: ignore[arg-type]
    )
    app_context.render(many(found, PULL_REQUESTS, id_key="id"))


@APP.command(help="Show a pull request.")
@handle_errors
def get(ctx: typer.Context, pr_id: PullRequestId, repo: Repo) -> None:
    app_context = get_app_context(ctx)
    pull_request = app_context.repository(repo).pull_requests.get(pr_id)
    app_context.render(single(pull_request, PULL_REQUEST, id_key="id"))


@APP.command(help="Open a pull request.")
@handle_errors
@options_from(_CreateOptions)
def create(ctx: typer.Context, options: _CreateOptions) -> None:
    app_context = get_app_context(ctx)
    payload = build(
        PullRequestCreate,
        options.from_file,
        title=options.title,
        source={"branch": {"name": options.source}} if options.source else None,
        destination={"branch": {"name": options.destination}} if options.destination else None,
        description=options.description,
        reviewers=[{"uuid": uuid} for uuid in options.reviewers] if options.reviewers else None,
        close_source_branch=options.close_source_branch,
    )
    created = app_context.repository(options.repo).pull_requests.create(payload)
    app_context.render(single(created, PULL_REQUEST, id_key="id"))


@APP.command(help="Update a pull request.")
@handle_errors
@options_from(_UpdateOptions)
def update(ctx: typer.Context, options: _UpdateOptions) -> None:
    app_context = get_app_context(ctx)
    payload = build(
        PullRequestUpdate,
        options.from_file,
        title=options.title,
        destination={"branch": {"name": options.destination}} if options.destination else None,
        description=options.description,
        reviewers=[{"uuid": uuid} for uuid in options.reviewers] if options.reviewers else None,
    )
    updated = app_context.repository(options.repo).pull_requests.update(options.pr_id, payload)
    app_context.render(single(updated, PULL_REQUEST, id_key="id"))


@APP.command(help="Approve a pull request.")
@handle_errors
def approve(ctx: typer.Context, pr_id: PullRequestId, repo: Repo) -> None:
    app_context = get_app_context(ctx)
    account = app_context.repository(repo).pull_requests.approve(pr_id)
    app_context.render(single(account, ACCOUNTS, id_key="account_id"))


@APP.command(help="Withdraw your approval.")
@handle_errors
def unapprove(ctx: typer.Context, pr_id: PullRequestId, repo: Repo) -> None:
    app_context = get_app_context(ctx)
    app_context.repository(repo).pull_requests.unapprove(pr_id)
    app_context.notify(f"Withdrew approval of pull request {pr_id}.")


@APP.command(name="request-changes", help="Request changes on a pull request.")
@handle_errors
def request_changes(ctx: typer.Context, pr_id: PullRequestId, repo: Repo) -> None:
    app_context = get_app_context(ctx)
    account = app_context.repository(repo).pull_requests.request_changes(pr_id)
    app_context.render(single(account, ACCOUNTS, id_key="account_id"))


@APP.command(name="unrequest-changes", help="Withdraw your change request.")
@handle_errors
def unrequest_changes(ctx: typer.Context, pr_id: PullRequestId, repo: Repo) -> None:
    app_context = get_app_context(ctx)
    app_context.repository(repo).pull_requests.unrequest_changes(pr_id)
    app_context.notify(f"Withdrew the change request on pull request {pr_id}.")


@APP.command(help="Decline a pull request.")
@handle_errors
def decline(ctx: typer.Context, pr_id: PullRequestId, repo: Repo) -> None:
    app_context = get_app_context(ctx)
    declined = app_context.repository(repo).pull_requests.decline(pr_id)
    app_context.render(single(declined, PULL_REQUEST, id_key="id"))


@APP.command(help="Merge a pull request.")
@handle_errors
@options_from(_MergeOptions)
def merge(ctx: typer.Context, options: _MergeOptions) -> None:
    app_context = get_app_context(ctx)
    requests = app_context.repository(options.repo).pull_requests
    payload = build(
        MergeParameters,
        message=options.message,
        merge_strategy=options.strategy.value if options.strategy else None,
        close_source_branch=options.close_source_branch,
    )
    if options.wait:
        status = requests.merge_and_wait(options.pr_id, payload, timeout=options.timeout)
        app_context.render(single(status, MERGE_STATUS, id_key="task_status"))
    else:
        app_context.render(single(requests.merge(options.pr_id, payload), MERGE_TASK, id_key="task_id"))


@APP.command(name="merge-status", help="Show the state of an asynchronous merge.")
@handle_errors
def merge_status(
    ctx: typer.Context,
    pr_id: PullRequestId,
    task_id: Annotated[str, typer.Argument(help="Task ID printed by `pr merge`.")],
    repo: Repo,
) -> None:
    app_context = get_app_context(ctx)
    status = app_context.repository(repo).pull_requests.merge_task_status(pr_id, task_id)
    app_context.render(single(status, MERGE_STATUS, id_key="task_status"))


@APP.command(help="List the merge checks of a pull request.")
@handle_errors
@options_from(_ChecksOptions)
def checks(ctx: typer.Context, options: _ChecksOptions) -> None:
    app_context = get_app_context(ctx)
    found = app_context.repository(options.repo).pull_requests.mergeability_checks(options.pr_id, q=options.query)
    app_context.render(many(found, CHECKS, id_key="uuid"))


@APP.command(help="Print the diff of a pull request.")
@handle_errors
def diff(ctx: typer.Context, pr_id: PullRequestId, repo: Repo) -> None:
    app_context = get_app_context(ctx)
    app_context.write(app_context.repository(repo).pull_requests.diff(pr_id))


@APP.command(help="Print the patch of a pull request.")
@handle_errors
def patch(ctx: typer.Context, pr_id: PullRequestId, repo: Repo) -> None:
    app_context = get_app_context(ctx)
    app_context.write(app_context.repository(repo).pull_requests.patch(pr_id))


@APP.command(help="List the files a pull request changes.")
@handle_errors
@options_from(_PagedPullRequest)
def files(ctx: typer.Context, options: _PagedPullRequest) -> None:
    app_context = get_app_context(ctx)
    requests = app_context.repository(options.repo).pull_requests
    found = paged(
        app_context,
        options,
        lambda: requests.diffstat(options.pr_id),
        lambda **page: requests.diffstat_page(options.pr_id, **page),
    )
    app_context.render(many(found, DIFFSTATS, id_key="new.path"))


@APP.command(help="List the commits of a pull request.")
@handle_errors
@options_from(_PagedPullRequest)
def commits(ctx: typer.Context, options: _PagedPullRequest) -> None:
    app_context = get_app_context(ctx)
    requests = app_context.repository(options.repo).pull_requests
    found = paged(
        app_context,
        options,
        lambda: requests.commits(options.pr_id),
        lambda **page: requests.commits_page(options.pr_id, **page),
    )
    app_context.render(many(found, COMMITS, id_key="hash"))


@APP.command(help="List the merge conflicts of a pull request.")
@handle_errors
@options_from(_PagedPullRequest)
def conflicts(ctx: typer.Context, options: _PagedPullRequest) -> None:
    app_context = get_app_context(ctx)
    requests = app_context.repository(options.repo).pull_requests
    found = paged(
        app_context,
        options,
        lambda: requests.conflicts(options.pr_id),
        lambda **page: requests.conflicts_page(options.pr_id, **page),
    )
    app_context.render(many(found, CONFLICTS, id_key="path"))


@APP.command(help="List the activity of a pull request, or of every pull request in the repository.")
@handle_errors
@options_from(_ActivityOptions)
def activity(ctx: typer.Context, options: _ActivityOptions) -> None:
    app_context = get_app_context(ctx)
    pr_id = options.pr_id
    if pr_id is None:
        repositories = app_context.workspace().repositories
        found = paged(
            app_context,
            options,
            lambda: repositories.pull_request_activity(options.repo),
            lambda **page: repositories.pull_request_activity_page(options.repo, **page),
        )
    else:
        requests = app_context.repository(options.repo).pull_requests
        found = paged(
            app_context,
            options,
            lambda: requests.activity(pr_id),
            lambda **page: requests.activity_page(pr_id, **page),
        )
    app_context.render(many(found, ACTIVITIES))

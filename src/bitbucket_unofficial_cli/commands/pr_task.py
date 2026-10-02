from dataclasses import dataclass
from enum import StrEnum
from typing import Annotated
from typing import Final

import typer
from bitbucket.models.task import TaskCreate
from bitbucket.models.task import TaskUpdate

from bitbucket_unofficial_cli.output.columns import TASKS
from bitbucket_unofficial_cli.output.renderer import many
from bitbucket_unofficial_cli.output.renderer import single
from bitbucket_unofficial_cli.runtime.context import get_app_context
from bitbucket_unofficial_cli.runtime.errors import handle_errors
from bitbucket_unofficial_cli.runtime.params import FromFile
from bitbucket_unofficial_cli.runtime.params import PagingOptions
from bitbucket_unofficial_cli.runtime.params import PullRequestId
from bitbucket_unofficial_cli.runtime.params import Repo
from bitbucket_unofficial_cli.runtime.params import Yes
from bitbucket_unofficial_cli.runtime.params import options_from
from bitbucket_unofficial_cli.services.listing import paged
from bitbucket_unofficial_cli.services.payloads import build

APP: Final = typer.Typer(help="Manage the tasks of a pull request.", no_args_is_help=True)

TaskId = Annotated[int, typer.Argument(help="Task ID.")]  # pylint: disable=gajaguar-module-const-naming,gajaguar-require-final
_Content = Annotated[str | None, typer.Option("--content", "-m", help="Task text.")]  # pylint: disable=gajaguar-module-const-naming,gajaguar-require-final


class _State(StrEnum):
    RESOLVED = "RESOLVED"
    UNRESOLVED = "UNRESOLVED"


@dataclass(frozen=True, slots=True, kw_only=True)
class _ListOptions(PagingOptions):
    repo: Repo
    pr_id: PullRequestId


@dataclass(frozen=True, slots=True, kw_only=True)
class _CreateOptions:
    repo: Repo
    pr_id: PullRequestId
    content: _Content = None
    pending: Annotated[bool | None, typer.Option("--pending/--no-pending", help="Create it as pending.")] = None
    from_file: FromFile = None


@dataclass(frozen=True, slots=True, kw_only=True)
class _UpdateOptions:
    repo: Repo
    pr_id: PullRequestId
    task_id: TaskId
    content: _Content = None
    state: Annotated[_State | None, typer.Option("--state", help="Resolve or reopen the task.")] = None
    from_file: FromFile = None


@APP.command(name="list", help="List the tasks of a pull request.")
@handle_errors
@options_from(_ListOptions)
def list_tasks(ctx: typer.Context, options: _ListOptions) -> None:
    app_context = get_app_context(ctx)
    tasks = app_context.repository(options.repo).pull_requests.tasks(options.pr_id)
    found = paged(app_context, options, tasks.list, tasks.list_page)
    app_context.render(many(found, TASKS, id_key="id"))


@APP.command(help="Show a task.")
@handle_errors
def get(ctx: typer.Context, pr_id: PullRequestId, task_id: TaskId, repo: Repo) -> None:
    app_context = get_app_context(ctx)
    task = app_context.repository(repo).pull_requests.tasks(pr_id).get(task_id)
    app_context.render(single(task, TASKS, id_key="id"))


@APP.command(help="Add a task.")
@handle_errors
@options_from(_CreateOptions)
def create(ctx: typer.Context, options: _CreateOptions) -> None:
    app_context = get_app_context(ctx)
    payload = build(
        TaskCreate,
        options.from_file,
        content={"raw": options.content} if options.content is not None else None,
        pending=options.pending,
    )
    tasks = app_context.repository(options.repo).pull_requests.tasks(options.pr_id)
    app_context.render(single(tasks.create(payload), TASKS, id_key="id"))


@APP.command(help="Edit, resolve or reopen a task.")
@handle_errors
@options_from(_UpdateOptions)
def update(ctx: typer.Context, options: _UpdateOptions) -> None:
    app_context = get_app_context(ctx)
    payload = build(
        TaskUpdate,
        options.from_file,
        content={"raw": options.content} if options.content is not None else None,
        state=options.state.value if options.state else None,
    )
    tasks = app_context.repository(options.repo).pull_requests.tasks(options.pr_id)
    app_context.render(single(tasks.update(options.task_id, payload), TASKS, id_key="id"))


@APP.command(help="Delete a task.")
@handle_errors
def delete(ctx: typer.Context, pr_id: PullRequestId, task_id: TaskId, repo: Repo, *, yes: Yes = False) -> None:
    app_context = get_app_context(ctx)
    app_context.confirm(f"Delete task {task_id}?", assume_yes=yes)
    app_context.repository(repo).pull_requests.tasks(pr_id).delete(task_id)
    app_context.notify(f"Deleted task {task_id}.")

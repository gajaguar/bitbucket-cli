from dataclasses import dataclass
from typing import Annotated
from typing import Final

import typer
from bitbucket.models.pipeline_config import PipelineScheduleCreate
from bitbucket.models.pipeline_config import PipelineScheduleUpdate

from bitbucket_unofficial_cli.output.columns import SCHEDULES
from bitbucket_unofficial_cli.output.columns import SCHEDULE_EXECUTIONS
from bitbucket_unofficial_cli.output.renderer import many
from bitbucket_unofficial_cli.output.renderer import single
from bitbucket_unofficial_cli.runtime.context import get_app_context
from bitbucket_unofficial_cli.runtime.errors import handle_errors
from bitbucket_unofficial_cli.runtime.params import FromFile
from bitbucket_unofficial_cli.runtime.params import PagingOptions
from bitbucket_unofficial_cli.runtime.params import Repo
from bitbucket_unofficial_cli.runtime.params import Yes
from bitbucket_unofficial_cli.runtime.params import options_from
from bitbucket_unofficial_cli.services.listing import paged
from bitbucket_unofficial_cli.services.payloads import build

APP: Final = typer.Typer(help="Scheduled pipelines of a repository.", no_args_is_help=True)

Uuid = Annotated[str, typer.Argument(help="Schedule UUID.")]  # pylint: disable=gajaguar-module-const-naming,gajaguar-require-final


@dataclass(frozen=True, slots=True, kw_only=True)
class _ListOptions(PagingOptions):
    repo: Repo


@dataclass(frozen=True, slots=True, kw_only=True)
class _ExecutionsOptions(_ListOptions):
    uuid: Uuid


@dataclass(frozen=True, slots=True, kw_only=True)
class _CreateOptions:
    repo: Repo
    ref_name: Annotated[str | None, typer.Option("--ref-name", help="Branch or tag to run on.")] = None
    ref_type: Annotated[str, typer.Option("--ref-type", help="branch or tag.")] = "branch"
    selector_type: Annotated[
        str, typer.Option("--selector-type", help="branches, tags, bookmarks, default or custom.")
    ] = "custom"
    pattern: Annotated[str | None, typer.Option("--pattern", help="Pipeline name, or branch pattern.")] = None
    cron: Annotated[str | None, typer.Option("--cron", help="Cron expression, e.g. '0 0 12 * * ? *'.")] = None
    enabled: Annotated[bool | None, typer.Option("--enabled/--disabled", help="Whether it runs.")] = None
    from_file: FromFile = None


@dataclass(frozen=True, slots=True, kw_only=True)
class _UpdateOptions:
    repo: Repo
    uuid: Uuid
    enabled: Annotated[bool, typer.Option("--enabled/--disabled", help="Whether it runs.")]


@dataclass(frozen=True, slots=True, kw_only=True)
class _DeleteOptions:
    repo: Repo
    uuid: Uuid
    yes: Yes = False


@APP.command(name="list", help="List the schedules of a repository.")
@handle_errors
@options_from(_ListOptions)
def list_schedules(ctx: typer.Context, options: _ListOptions) -> None:
    app_context = get_app_context(ctx)
    schedules = app_context.repository(options.repo).pipelines_config.schedules
    found = paged(app_context, options, schedules.list, schedules.list_page)
    app_context.render(many(found, SCHEDULES, id_key="uuid"))


@APP.command(help="Show a schedule.")
@handle_errors
def get(ctx: typer.Context, uuid: Uuid, repo: Repo) -> None:
    app_context = get_app_context(ctx)
    schedule = app_context.repository(repo).pipelines_config.schedules.get(uuid)
    app_context.render(single(schedule, SCHEDULES, id_key="uuid"))


@APP.command(help="Add a schedule.")
@handle_errors
@options_from(_CreateOptions)
def create(ctx: typer.Context, options: _CreateOptions) -> None:
    app_context = get_app_context(ctx)
    target = {
        "type": "pipeline_ref_target",
        "ref_type": options.ref_type,
        "ref_name": options.ref_name,
        "selector": {"type": options.selector_type, "pattern": options.pattern},
    }
    payload = build(
        PipelineScheduleCreate,
        options.from_file,
        target=target if options.ref_name else None,
        cron_pattern=options.cron,
        enabled=options.enabled,
    )
    created = app_context.repository(options.repo).pipelines_config.schedules.create(payload)
    app_context.render(single(created, SCHEDULES, id_key="uuid"))


@APP.command(help="Turn a schedule on or off.")
@handle_errors
@options_from(_UpdateOptions)
def update(ctx: typer.Context, options: _UpdateOptions) -> None:
    app_context = get_app_context(ctx)
    schedules = app_context.repository(options.repo).pipelines_config.schedules
    updated = schedules.update(options.uuid, build(PipelineScheduleUpdate, enabled=options.enabled))
    app_context.render(single(updated, SCHEDULES, id_key="uuid"))


@APP.command(help="Delete a schedule.")
@handle_errors
@options_from(_DeleteOptions)
def delete(ctx: typer.Context, options: _DeleteOptions) -> None:
    app_context = get_app_context(ctx)
    app_context.confirm(f"Delete schedule '{options.uuid}'?", assume_yes=options.yes)
    app_context.repository(options.repo).pipelines_config.schedules.delete(options.uuid)
    app_context.notify(f"Deleted schedule '{options.uuid}'.")


@APP.command(help="List the runs of a schedule.")
@handle_errors
@options_from(_ExecutionsOptions)
def executions(ctx: typer.Context, options: _ExecutionsOptions) -> None:
    app_context = get_app_context(ctx)
    schedules = app_context.repository(options.repo).pipelines_config.schedules
    found = paged(
        app_context,
        options,
        lambda: schedules.executions(options.uuid),
        lambda **page: schedules.executions_page(options.uuid, **page),
    )
    app_context.render(many(found, SCHEDULE_EXECUTIONS))

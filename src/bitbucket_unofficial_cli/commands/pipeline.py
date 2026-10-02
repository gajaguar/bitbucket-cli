import json
from dataclasses import dataclass
from typing import Annotated
from typing import Final

import typer
from bitbucket.models.pipeline import PipelineCreate

from bitbucket_unofficial_cli.commands import pipeline_runner
from bitbucket_unofficial_cli.commands import pipeline_schedule
from bitbucket_unofficial_cli.commands import pipeline_settings
from bitbucket_unofficial_cli.commands import pipeline_variable
from bitbucket_unofficial_cli.output.columns import PIPELINES
from bitbucket_unofficial_cli.output.columns import PIPELINE_STEPS
from bitbucket_unofficial_cli.output.renderer import many
from bitbucket_unofficial_cli.output.renderer import single
from bitbucket_unofficial_cli.runtime.context import get_app_context
from bitbucket_unofficial_cli.runtime.errors import CliError
from bitbucket_unofficial_cli.runtime.errors import handle_errors
from bitbucket_unofficial_cli.runtime.exit_codes import ExitCode
from bitbucket_unofficial_cli.runtime.params import FromFile
from bitbucket_unofficial_cli.runtime.params import PagingOptions
from bitbucket_unofficial_cli.runtime.params import Repo
from bitbucket_unofficial_cli.runtime.params import options_from
from bitbucket_unofficial_cli.services.listing import paged
from bitbucket_unofficial_cli.services.payloads import build
from bitbucket_unofficial_cli.services.secrets import value_from_environment

APP: Final = typer.Typer(help="Run and inspect pipelines, and configure them.", no_args_is_help=True)
APP.add_typer(pipeline_settings.CONFIG_APP, name="config")
APP.add_typer(pipeline_settings.KEY_APP, name="ssh-key")
APP.add_typer(pipeline_settings.HOST_APP, name="known-host")
APP.add_typer(pipeline_settings.CACHE_APP, name="cache")
APP.add_typer(pipeline_variable.APP, name="variable")
APP.add_typer(pipeline_schedule.APP, name="schedule")
APP.add_typer(pipeline_runner.APP, name="runner")

PipelineUuid = Annotated[str, typer.Argument(help="Pipeline UUID.")]  # pylint: disable=gajaguar-module-const-naming,gajaguar-require-final
StepUuid = Annotated[str, typer.Argument(help="Step UUID.")]  # pylint: disable=gajaguar-module-const-naming,gajaguar-require-final


@dataclass(frozen=True, slots=True, kw_only=True)
class _ListOptions(PagingOptions):
    repo: Repo
    branch: Annotated[str | None, typer.Option("--branch", help="Only pipelines of this branch.")] = None
    tag: Annotated[str | None, typer.Option("--tag", help="Only pipelines of this tag.")] = None
    status: Annotated[str | None, typer.Option("--status", help="Only pipelines in this state.")] = None
    sort: Annotated[str | None, typer.Option("--sort", help="Field to sort by; prefix with - to reverse.")] = None
    filters: Annotated[
        list[str] | None,
        typer.Option("--filter", help="Any other Bitbucket filter as NAME=VALUE; repeatable."),
    ] = None


@dataclass(frozen=True, slots=True, kw_only=True)
class _RunOptions:
    repo: Repo
    branch: Annotated[str | None, typer.Option("--branch", help="Run on this branch.")] = None
    tag: Annotated[str | None, typer.Option("--tag", help="Run on this tag.")] = None
    commit: Annotated[str | None, typer.Option("--commit", help="Run on this commit hash.")] = None
    custom: Annotated[str | None, typer.Option("--custom", help="Name of a custom pipeline to run.")] = None
    variables: Annotated[
        list[str] | None,
        typer.Option("--variable-env", help="Pass the environment variable of this name as a variable; repeatable."),
    ] = None
    secured: Annotated[
        list[str] | None,
        typer.Option("--secured-variable-env", help="Like --variable-env, as a secured variable; repeatable."),
    ] = None
    merge_defaults: Annotated[bool, typer.Option("--merge-defaults", help="Merge the default variables.")] = False
    create_branch: Annotated[str | None, typer.Option("--create-branch", help="Create this branch to run on.")] = None
    from_file: FromFile = None


@dataclass(frozen=True, slots=True, kw_only=True)
class _PipelineOptions:
    repo: Repo
    pipeline: PipelineUuid


@dataclass(frozen=True, slots=True, kw_only=True)
class _StepsOptions(PagingOptions):
    repo: Repo
    pipeline: PipelineUuid


@dataclass(frozen=True, slots=True, kw_only=True)
class _StepOptions:
    repo: Repo
    pipeline: PipelineUuid
    step: StepUuid


@dataclass(frozen=True, slots=True, kw_only=True)
class _LogOptions(_StepOptions):
    container: Annotated[str | None, typer.Option("--container", help="Log UUID of a service container.")] = None
    start: Annotated[int | None, typer.Option("--start", help="First byte to fetch.")] = None
    end: Annotated[int | None, typer.Option("--end", help="Last byte to fetch.")] = None


@dataclass(frozen=True, slots=True, kw_only=True)
class _CaseOptions(_StepOptions):
    case: Annotated[str, typer.Argument(help="Test case UUID.")]


def _list_params(options: _ListOptions) -> dict[str, str]:
    params = {
        "sort": options.sort,
        "status": options.status,
        "target.branch": options.branch,
        "target.tag": options.tag,
    }
    found = {name: value for name, value in params.items() if value is not None}
    for item in options.filters or []:
        name, separator, value = item.partition("=")
        if not separator:
            message = f"--filter expects NAME=VALUE, got {item!r}."
            raise CliError(message, exit_code=ExitCode.USAGE)
        found[name] = value
    return found


def _target(options: _RunOptions) -> dict[str, object] | None:
    selector = {"type": "custom", "pattern": options.custom} if options.custom else None
    commit = {"hash": options.commit} if options.commit else None
    if options.branch or options.tag:
        ref_type, ref_name = ("branch", options.branch) if options.branch else ("tag", options.tag)
        target: dict[str, object] = {"type": "pipeline_ref_target", "ref_type": ref_type, "ref_name": ref_name}
        if commit:
            target["commit"] = commit
    elif commit:
        target = {"type": "pipeline_commit_target", "commit": commit}
    else:
        return None
    if selector:
        target["selector"] = selector
    return target


def _variables(options: _RunOptions) -> list[dict[str, object]] | None:
    found: list[dict[str, object]] = [
        {"key": name, "value": value_from_environment(name)} for name in options.variables or []
    ]
    found += [{"key": name, "value": value_from_environment(name), "secured": True} for name in options.secured or []]
    return found or None


@APP.command(name="list", help="List the pipelines of a repository, newest first.")
@handle_errors
@options_from(_ListOptions)
def list_pipelines(ctx: typer.Context, options: _ListOptions) -> None:
    app_context = get_app_context(ctx)
    pipelines = app_context.repository(options.repo).pipelines
    params = _list_params(options)
    found = paged(
        app_context,
        options,
        lambda: pipelines.list(**params),
        lambda **page: pipelines.list_page(**params, **page),
    )
    app_context.render(many(found, PIPELINES, id_key="uuid"))


@APP.command(help="Show a pipeline.")
@handle_errors
@options_from(_PipelineOptions)
def get(ctx: typer.Context, options: _PipelineOptions) -> None:
    app_context = get_app_context(ctx)
    pipeline = app_context.repository(options.repo).pipelines.get(options.pipeline)
    app_context.render(single(pipeline, PIPELINES, id_key="uuid"))


@APP.command(help="Start a pipeline on a branch, tag or commit.")
@handle_errors
@options_from(_RunOptions)
def run(ctx: typer.Context, options: _RunOptions) -> None:
    app_context = get_app_context(ctx)
    payload = build(PipelineCreate, options.from_file, target=_target(options), variables=_variables(options))
    pipeline = app_context.repository(options.repo).pipelines.create(
        payload,
        merge_defaults=True if options.merge_defaults else None,
        target_branch_to_create=options.create_branch,
    )
    app_context.render(single(pipeline, PIPELINES, id_key="uuid"))


@APP.command(help="Stop a running pipeline.")
@handle_errors
@options_from(_PipelineOptions)
def stop(ctx: typer.Context, options: _PipelineOptions) -> None:
    app_context = get_app_context(ctx)
    app_context.repository(options.repo).pipelines.stop(options.pipeline)
    app_context.notify(f"Stopped pipeline {options.pipeline}.")


@APP.command(help="List the steps of a pipeline.")
@handle_errors
@options_from(_StepsOptions)
def steps(ctx: typer.Context, options: _StepsOptions) -> None:
    app_context = get_app_context(ctx)
    pipelines = app_context.repository(options.repo).pipelines
    found = paged(
        app_context,
        options,
        lambda: pipelines.steps(options.pipeline),
        lambda **page: pipelines.steps_page(options.pipeline, **page),
    )
    app_context.render(many(found, PIPELINE_STEPS, id_key="uuid"))


@APP.command(help="Show a step of a pipeline.")
@handle_errors
@options_from(_StepOptions)
def step(ctx: typer.Context, options: _StepOptions) -> None:
    app_context = get_app_context(ctx)
    found = app_context.repository(options.repo).pipelines.step(options.pipeline, options.step)
    app_context.render(single(found, PIPELINE_STEPS, id_key="uuid"))


@APP.command(help="Print the log of a step, or of one of its service containers.")
@handle_errors
@options_from(_LogOptions)
def log(ctx: typer.Context, options: _LogOptions) -> None:
    app_context = get_app_context(ctx)
    pipelines = app_context.repository(options.repo).pipelines
    if options.container:
        content = pipelines.container_log(options.pipeline, options.step, options.container)
    else:
        content = pipelines.step_log(options.pipeline, options.step, start=options.start, end=options.end)
    app_context.write_bytes(content)


@APP.command(help="Print the test report summary of a step as JSON.")
@handle_errors
@options_from(_StepOptions)
def tests(ctx: typer.Context, options: _StepOptions) -> None:
    app_context = get_app_context(ctx)
    report = app_context.repository(options.repo).pipelines.test_reports(options.pipeline, options.step)
    app_context.write(json.dumps(report, indent=2))


@APP.command(name="test-cases", help="Print the test cases of a step as JSON.")
@handle_errors
@options_from(_StepOptions)
def test_cases(ctx: typer.Context, options: _StepOptions) -> None:
    app_context = get_app_context(ctx)
    cases = app_context.repository(options.repo).pipelines.test_cases(options.pipeline, options.step)
    app_context.write(json.dumps(cases, indent=2))


@APP.command(name="test-case-reasons", help="Print why a test case failed, as JSON.")
@handle_errors
@options_from(_CaseOptions)
def test_case_reasons(ctx: typer.Context, options: _CaseOptions) -> None:
    app_context = get_app_context(ctx)
    pipelines = app_context.repository(options.repo).pipelines
    app_context.write(json.dumps(pipelines.test_case_reasons(options.pipeline, options.step, options.case), indent=2))

from dataclasses import dataclass
from enum import StrEnum
from typing import Annotated
from typing import Final

import typer
from bitbucket.models.report import ReportAnnotationWrite

from bitbucket_unofficial_cli.output.columns import ANNOTATIONS
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
from bitbucket_unofficial_cli.services.payloads import build_many

APP: Final = typer.Typer(help="Manage the annotations of a code insight report.", no_args_is_help=True)

CommitHash = Annotated[str, typer.Argument(help="Commit hash.")]  # pylint: disable=gajaguar-module-const-naming,gajaguar-require-final
ReportId = Annotated[str, typer.Argument(help="Report ID.")]  # pylint: disable=gajaguar-module-const-naming,gajaguar-require-final
AnnotationId = Annotated[str, typer.Argument(help="Annotation ID, chosen by the reporter.")]  # pylint: disable=gajaguar-module-const-naming,gajaguar-require-final


class _Type(StrEnum):
    VULNERABILITY = "VULNERABILITY"
    CODE_SMELL = "CODE_SMELL"
    BUG = "BUG"


class _Result(StrEnum):
    PASSED = "PASSED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"
    IGNORED = "IGNORED"


class _Severity(StrEnum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


@dataclass(frozen=True, slots=True, kw_only=True)
class _ListOptions(PagingOptions):
    repo: Repo
    commit: CommitHash
    report_id: ReportId


@dataclass(frozen=True, slots=True, kw_only=True)
class _PutOptions:
    repo: Repo
    commit: CommitHash
    report_id: ReportId
    annotation_id: AnnotationId
    title: Annotated[str | None, typer.Option("--title", help="Annotation title.")] = None
    summary: Annotated[str | None, typer.Option("--summary", help="One-line summary.")] = None
    details: Annotated[str | None, typer.Option("--details", help="Longer description.")] = None
    path: Annotated[str | None, typer.Option("--path", help="File the annotation points at.")] = None
    line: Annotated[int | None, typer.Option("--line", help="Line in that file.")] = None
    annotation_type: Annotated[_Type | None, typer.Option("--type", help="Kind of finding.")] = None
    result: Annotated[_Result | None, typer.Option("--result", help="Result of the check.")] = None
    severity: Annotated[_Severity | None, typer.Option("--severity", help="Severity.")] = None
    link: Annotated[str | None, typer.Option("--link", help="Link to more information.")] = None
    from_file: FromFile = None


@dataclass(frozen=True, slots=True, kw_only=True)
class _PutManyOptions:
    repo: Repo
    commit: CommitHash
    report_id: ReportId
    from_file: Annotated[str, typer.Option("--from-file", help="JSON array of 1 to 100 annotations, or - for stdin.")]


@APP.command(name="list", help="List the annotations of a report.")
@handle_errors
@options_from(_ListOptions)
def list_annotations(ctx: typer.Context, options: _ListOptions) -> None:
    app_context = get_app_context(ctx)
    annotations = app_context.repository(options.repo).commits.reports(options.commit).annotations(options.report_id)
    found = paged(app_context, options, annotations.list, annotations.list_page)
    app_context.render(many(found, ANNOTATIONS, id_key="external_id"))


@APP.command(help="Show an annotation.")
@handle_errors
def get(ctx: typer.Context, commit: CommitHash, report_id: ReportId, annotation_id: AnnotationId, repo: Repo) -> None:
    app_context = get_app_context(ctx)
    annotations = app_context.repository(repo).commits.reports(commit).annotations(report_id)
    app_context.render(single(annotations.get(annotation_id), ANNOTATIONS, id_key="external_id"))


@APP.command(help="Create or replace an annotation.")
@handle_errors
@options_from(_PutOptions)
def put(ctx: typer.Context, options: _PutOptions) -> None:
    app_context = get_app_context(ctx)
    payload = build(
        ReportAnnotationWrite,
        options.from_file,
        title=options.title,
        summary=options.summary,
        details=options.details,
        path=options.path,
        line=options.line,
        annotation_type=options.annotation_type.value if options.annotation_type else None,
        result=options.result.value if options.result else None,
        severity=options.severity.value if options.severity else None,
        link=options.link,
    )
    annotations = app_context.repository(options.repo).commits.reports(options.commit).annotations(options.report_id)
    app_context.render(single(annotations.put(options.annotation_id, payload), ANNOTATIONS, id_key="external_id"))


@APP.command(name="put-many", help="Create or replace up to 100 annotations from a JSON array.")
@handle_errors
@options_from(_PutManyOptions)
def put_many(ctx: typer.Context, options: _PutManyOptions) -> None:
    app_context = get_app_context(ctx)
    payloads = build_many(ReportAnnotationWrite, options.from_file)
    annotations = app_context.repository(options.repo).commits.reports(options.commit).annotations(options.report_id)
    app_context.render(many(annotations.put_many(payloads), ANNOTATIONS, id_key="external_id"))


@dataclass(frozen=True, slots=True, kw_only=True)
class _DeleteOptions:
    repo: Repo
    commit: CommitHash
    report_id: ReportId
    annotation_id: AnnotationId
    yes: Yes = False


@APP.command(help="Delete an annotation.")
@handle_errors
@options_from(_DeleteOptions)
def delete(ctx: typer.Context, options: _DeleteOptions) -> None:
    app_context = get_app_context(ctx)
    app_context.confirm(f"Delete annotation '{options.annotation_id}'?", assume_yes=options.yes)
    reports = app_context.repository(options.repo).commits.reports(options.commit)
    reports.annotations(options.report_id).delete(options.annotation_id)
    app_context.notify(f"Deleted annotation '{options.annotation_id}'.")

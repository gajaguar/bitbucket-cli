from dataclasses import dataclass
from enum import StrEnum
from typing import Annotated
from typing import Final

import typer
from bitbucket.models.report import ReportWrite

from bitbucket_unofficial_cli.output.columns import REPORT
from bitbucket_unofficial_cli.output.columns import REPORTS
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

APP: Final = typer.Typer(help="Manage the code insight reports of a commit.", no_args_is_help=True)

CommitHash = Annotated[str, typer.Argument(help="Commit hash.")]  # pylint: disable=gajaguar-module-const-naming,gajaguar-require-final
ReportId = Annotated[str, typer.Argument(help="Report ID, chosen by the reporter.")]  # pylint: disable=gajaguar-module-const-naming,gajaguar-require-final


class _ReportType(StrEnum):
    SECURITY = "SECURITY"
    COVERAGE = "COVERAGE"
    TEST = "TEST"
    BUG = "BUG"


class _Result(StrEnum):
    PASSED = "PASSED"
    FAILED = "FAILED"
    PENDING = "PENDING"


@dataclass(frozen=True, slots=True, kw_only=True)
class _ListOptions(PagingOptions):
    repo: Repo
    commit: CommitHash


@dataclass(frozen=True, slots=True, kw_only=True)
class _PutOptions:
    repo: Repo
    commit: CommitHash
    report_id: ReportId
    title: Annotated[str | None, typer.Option("--title", help="Report title.")] = None
    details: Annotated[str | None, typer.Option("--details", help="Report details.")] = None
    reporter: Annotated[str | None, typer.Option("--reporter", help="Name of the tool reporting.")] = None
    link: Annotated[str | None, typer.Option("--link", help="Link to the full report.")] = None
    report_type: Annotated[_ReportType | None, typer.Option("--type", help="Kind of report.")] = None
    result: Annotated[_Result | None, typer.Option("--result", help="Overall result.")] = None
    from_file: FromFile = None


@APP.command(name="list", help="List the reports of a commit.")
@handle_errors
@options_from(_ListOptions)
def list_reports(ctx: typer.Context, options: _ListOptions) -> None:
    app_context = get_app_context(ctx)
    reports = app_context.repository(options.repo).commits.reports(options.commit)
    found = paged(app_context, options, reports.list, reports.list_page)
    app_context.render(many(found, REPORTS, id_key="external_id"))


@APP.command(help="Show a report.")
@handle_errors
def get(ctx: typer.Context, commit: CommitHash, report_id: ReportId, repo: Repo) -> None:
    app_context = get_app_context(ctx)
    report = app_context.repository(repo).commits.reports(commit).get(report_id)
    app_context.render(single(report, REPORT, id_key="external_id"))


@APP.command(help="Create or replace a report.")
@handle_errors
@options_from(_PutOptions)
def put(ctx: typer.Context, options: _PutOptions) -> None:
    app_context = get_app_context(ctx)
    payload = build(
        ReportWrite,
        options.from_file,
        title=options.title,
        details=options.details,
        reporter=options.reporter,
        link=options.link,
        report_type=options.report_type.value if options.report_type else None,
        result=options.result.value if options.result else None,
    )
    reports = app_context.repository(options.repo).commits.reports(options.commit)
    app_context.render(single(reports.put(options.report_id, payload), REPORT, id_key="external_id"))


@APP.command(help="Delete a report.")
@handle_errors
def delete(ctx: typer.Context, commit: CommitHash, report_id: ReportId, repo: Repo, *, yes: Yes = False) -> None:
    app_context = get_app_context(ctx)
    app_context.confirm(f"Delete report '{report_id}'?", assume_yes=yes)
    app_context.repository(repo).commits.reports(commit).delete(report_id)
    app_context.notify(f"Deleted report '{report_id}'.")

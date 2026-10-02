from dataclasses import dataclass
from typing import Annotated
from typing import Final

import typer

from bitbucket_unofficial_cli.output.columns import CODE_SEARCH
from bitbucket_unofficial_cli.output.renderer import many
from bitbucket_unofficial_cli.runtime.context import get_app_context
from bitbucket_unofficial_cli.runtime.errors import CliError
from bitbucket_unofficial_cli.runtime.errors import handle_errors
from bitbucket_unofficial_cli.runtime.exit_codes import ExitCode
from bitbucket_unofficial_cli.runtime.params import PagingOptions
from bitbucket_unofficial_cli.runtime.params import options_from
from bitbucket_unofficial_cli.services.listing import paged

APP: Final = typer.Typer(help="Search code. Bitbucket deprecates code search on 2026-11-01.", no_args_is_help=True)


@dataclass(frozen=True, slots=True, kw_only=True)
class _CodeOptions(PagingOptions):
    query: Annotated[str, typer.Argument(help="Search query, e.g. 'lang:python def main'.")]
    user: Annotated[str | None, typer.Option("--user", help="Search a user's repositories instead.")] = None
    team: Annotated[str | None, typer.Option("--team", help="Search a team's repositories instead.")] = None
    fields: Annotated[str | None, typer.Option("--fields", help="Bitbucket partial-response fields.")] = None


@APP.command(help="Search the code of the workspace, a user or a team.")
@handle_errors
@options_from(_CodeOptions)
def code(ctx: typer.Context, options: _CodeOptions) -> None:
    app_context = get_app_context(ctx)
    if options.user and options.team:
        message = "--user and --team cannot be combined."
        raise CliError(message, exit_code=ExitCode.USAGE)
    if options.user:
        search = app_context.client().users(options.user).search
    elif options.team:
        search = app_context.client().teams(options.team).search
    else:
        search = app_context.workspace().search
    found = paged(
        app_context,
        options,
        lambda: search.code(options.query, fields=options.fields),
        lambda **page: search.code_page(options.query, fields=options.fields, **page),
    )
    app_context.render(many(found, CODE_SEARCH, id_key="file.path"))

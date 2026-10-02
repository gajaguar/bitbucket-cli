from typing import Annotated
from typing import Final

import typer

from bitbucket_unofficial_cli.output.columns import MEMBERS
from bitbucket_unofficial_cli.output.renderer import many
from bitbucket_unofficial_cli.output.renderer import single
from bitbucket_unofficial_cli.runtime.context import get_app_context
from bitbucket_unofficial_cli.runtime.errors import handle_errors
from bitbucket_unofficial_cli.runtime.params import PagingOptions
from bitbucket_unofficial_cli.runtime.params import options_from
from bitbucket_unofficial_cli.services.listing import paged

APP: Final = typer.Typer(help="Inspect the members of the selected workspace.", no_args_is_help=True)


@APP.command(name="list", help="List the workspace members.")
@handle_errors
@options_from(PagingOptions)
def list_members(ctx: typer.Context, options: PagingOptions) -> None:
    app_context = get_app_context(ctx)
    members = app_context.workspace().members
    found = paged(app_context, options, members.list, members.list_page)
    app_context.render(many(found, MEMBERS, id_key="user.account_id"))


@APP.command(help="Show one member by UUID or account ID.")
@handle_errors
def get(ctx: typer.Context, member: Annotated[str, typer.Argument(help="Member UUID or account ID.")]) -> None:
    app_context = get_app_context(ctx)
    app_context.render(single(app_context.workspace().members.get(member), MEMBERS, id_key="user.account_id"))

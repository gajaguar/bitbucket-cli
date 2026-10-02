from typing import Final

import typer

from bitbucket_unofficial_cli.output.columns import USERS
from bitbucket_unofficial_cli.output.renderer import single
from bitbucket_unofficial_cli.runtime.context import get_app_context
from bitbucket_unofficial_cli.runtime.errors import handle_errors

APP: Final = typer.Typer(help="Show the authenticated Bitbucket user.", no_args_is_help=True)


@APP.command(help="Show the user the credential belongs to.")
@handle_errors
def me(ctx: typer.Context) -> None:
    app_context = get_app_context(ctx)
    user = app_context.client().user.me()
    app_context.render(single(user, USERS, id_key="account_id"))

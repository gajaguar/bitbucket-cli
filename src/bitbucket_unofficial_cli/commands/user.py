from typing import Annotated
from typing import Final

import typer

from bitbucket_unofficial_cli.commands import user_keys
from bitbucket_unofficial_cli.commands import user_variable
from bitbucket_unofficial_cli.output.columns import USERS
from bitbucket_unofficial_cli.output.renderer import single
from bitbucket_unofficial_cli.runtime.context import get_app_context
from bitbucket_unofficial_cli.runtime.errors import handle_errors

APP: Final = typer.Typer(help="Show the authenticated Bitbucket user, or another one.", no_args_is_help=True)
APP.add_typer(user_keys.EMAIL_APP, name="email")
APP.add_typer(user_keys.SSH_APP, name="ssh-key")
APP.add_typer(user_keys.GPG_APP, name="gpg-key")
APP.add_typer(user_variable.APP, name="variable")


@APP.command(help="Show the user the credential belongs to.")
@handle_errors
def me(ctx: typer.Context) -> None:
    app_context = get_app_context(ctx)
    user = app_context.client().user.me()
    app_context.render(single(user, USERS, id_key="account_id"))


@APP.command(help="Show a user by account ID or UUID.")
@handle_errors
def get(ctx: typer.Context, user: Annotated[str, typer.Argument(help="Account ID or UUID.")]) -> None:
    app_context = get_app_context(ctx)
    app_context.render(single(app_context.client().users(user).get(), USERS, id_key="account_id"))

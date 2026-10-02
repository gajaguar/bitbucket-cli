from __future__ import annotations

from typing import TYPE_CHECKING

from bitbucket_unofficial_cli.runtime.errors import CliError
from bitbucket_unofficial_cli.runtime.exit_codes import ExitCode

if TYPE_CHECKING:
    from bitbucket_unofficial_cli.runtime.context import AppContext


# Bitbucket addresses a user's keys and variables by account ID; without --user it is the person the
# credential belongs to.
def selected_user(app_context: AppContext, user: str | None) -> str:
    if user:
        return user
    account_id = app_context.client().user.me().account_id
    if not account_id:
        message = "Bitbucket did not report the account ID of the current user; pass --user."
        raise CliError(message, exit_code=ExitCode.FAILURE)
    return str(account_id)


__all__ = ["selected_user"]

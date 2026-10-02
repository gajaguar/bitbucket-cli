from __future__ import annotations

import secrets
from dataclasses import dataclass
from typing import TYPE_CHECKING
from typing import Final

from bitbucket_unofficial_cli.auth.callback_server import CallbackServer
from bitbucket_unofficial_cli.auth.callback_server import parse_redirect
from bitbucket_unofficial_cli.auth.oauth import authorize_url
from bitbucket_unofficial_cli.runtime.errors import CliError
from bitbucket_unofficial_cli.runtime.exit_codes import ExitCode

if TYPE_CHECKING:
    from collections.abc import Callable

    from bitbucket_unofficial_cli.auth.callback_server import CallbackResult
    from bitbucket_unofficial_cli.auth.credentials import OAuthCredential
    from bitbucket_unofficial_cli.auth.oauth import OAuthClient
    from bitbucket_unofficial_cli.auth.oauth import OAuthConsumer

CALLBACK_TIMEOUT: Final = 300.0


# Everything that varies between the browser flow and the paste-the-URL flow is injected, so the
# command stays thin and tests drive both without a real browser or terminal.
@dataclass(frozen=True, slots=True)
class AuthorizationCodeFlow:
    oauth: OAuthClient
    open_browser: Callable[[str], object]
    notify: Callable[[str], None]
    read_redirect: Callable[[], str]
    timeout: float = CALLBACK_TIMEOUT

    def authorize(self, consumer: OAuthConsumer, *, port: int, use_browser: bool) -> OAuthCredential:
        state = secrets.token_urlsafe(24)
        url = authorize_url(consumer.client_id, state)
        result = self._browser_result(url, port) if use_browser else self._pasted_result(url)
        if result.error:
            message = f"Bitbucket denied the authorization: {result.error}"
            raise CliError(message, exit_code=ExitCode.AUTHENTICATION)
        if not secrets.compare_digest((result.state or "").encode(), state.encode()):
            message = "The authorization reply does not match this login (state mismatch)."
            raise CliError(message, exit_code=ExitCode.AUTHENTICATION)
        if not result.code:
            message = "The authorization reply carries no code."
            raise CliError(message, exit_code=ExitCode.AUTHENTICATION)
        return self.oauth.exchange_code(consumer, result.code)

    def _browser_result(self, url: str, port: int) -> CallbackResult:
        server = CallbackServer(port)
        try:
            self.notify(f"Opening your browser to authorize; if it does not open, visit:\n{url}")
            self.open_browser(url)
            return server.wait(self.timeout)
        finally:
            server.close()

    def _pasted_result(self, url: str) -> CallbackResult:
        self.notify(f"Open this URL, authorize, then paste the address you were redirected to:\n{url}")
        return parse_redirect(self.read_redirect().strip())

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import TYPE_CHECKING
from typing import Final
from urllib.parse import urlencode

import httpx

from bitbucket_unofficial_cli.auth.credentials import OAuthCredential
from bitbucket_unofficial_cli.auth.credentials import OAuthGrant
from bitbucket_unofficial_cli.runtime.errors import CliError
from bitbucket_unofficial_cli.runtime.exit_codes import ExitCode

if TYPE_CHECKING:
    from collections.abc import Callable

# The Bitbucket SDK leaves the OAuth dance to the application, so this module is the one place the
# CLI talks to Bitbucket without the SDK: the consumer's authorize and token endpoints.
AUTHORIZE_URL: Final = "https://bitbucket.org/site/oauth2/authorize"
TOKEN_URL: Final = "https://bitbucket.org/site/oauth2/access_token"  # ruff: ignore[hardcoded-password-string]
EXPIRY_MARGIN: Final = 60.0
HTTP_TIMEOUT: Final = 30.0
LOGIN_HINT: Final = "Run `bitbucket auth login --oauth` to authorize again."

type Clock = Callable[[], float]  # pylint: disable=gajaguar-module-const-naming
type HttpFactory = Callable[[], httpx.Client]  # pylint: disable=gajaguar-module-const-naming


def default_http() -> httpx.Client:
    return httpx.Client(timeout=HTTP_TIMEOUT)


@dataclass(frozen=True, slots=True)
class OAuthConsumer:
    client_id: str
    client_secret: str


# Bitbucket sends the user back to the callback URL configured on the consumer, so the
# authorize URL carries no redirect_uri; `state` is echoed back to bind the reply to this login.
def authorize_url(client_id: str, state: str) -> str:
    return f"{AUTHORIZE_URL}?{urlencode({'client_id': client_id, 'response_type': 'code', 'state': state})}"


def _failure(response: httpx.Response) -> CliError:
    detail = f"HTTP {response.status_code}"
    try:
        payload: object = response.json()
    except ValueError:
        payload = None
    if isinstance(payload, dict):
        text = payload.get("error_description") or payload.get("error")
        if isinstance(text, str):
            detail = f"{text} ({detail})"
    return CliError(f"Bitbucket rejected the OAuth request: {detail}.", exit_code=ExitCode.AUTHENTICATION)


class OAuthClient:
    def __init__(self, http: HttpFactory = default_http, clock: Clock = time.time) -> None:
        self._http = http
        self._clock = clock

    def exchange_code(self, consumer: OAuthConsumer, code: str) -> OAuthCredential:
        data = {"grant_type": "authorization_code", "code": code}
        return self._request(consumer, data, grant=OAuthGrant.AUTHORIZATION_CODE, previous_refresh=None)

    def client_credentials(self, consumer: OAuthConsumer) -> OAuthCredential:
        data = {"grant_type": "client_credentials"}
        return self._request(consumer, data, grant=OAuthGrant.CLIENT_CREDENTIALS, previous_refresh=None)

    # Client credentials have no refresh token, so renewing means asking again.
    def renew(self, credential: OAuthCredential) -> OAuthCredential:
        consumer = OAuthConsumer(credential.client_id, credential.client_secret)
        if credential.grant is OAuthGrant.CLIENT_CREDENTIALS:
            return self.client_credentials(consumer)
        if not credential.refresh_token:
            message = "The stored OAuth credential has no refresh token."
            raise CliError(message, exit_code=ExitCode.AUTHENTICATION, hint=LOGIN_HINT)
        data = {"grant_type": "refresh_token", "refresh_token": credential.refresh_token}
        try:
            return self._request(consumer, data, grant=credential.grant, previous_refresh=credential.refresh_token)
        except CliError as error:
            if error.exit_code is ExitCode.AUTHENTICATION:
                raise CliError(error.message, exit_code=error.exit_code, hint=LOGIN_HINT) from error
            raise

    def is_expired(self, credential: OAuthCredential) -> bool:
        return credential.expires_at > 0 and self._clock() >= credential.expires_at - EXPIRY_MARGIN

    def _request(
        self,
        consumer: OAuthConsumer,
        data: dict[str, str],
        *,
        grant: OAuthGrant,
        previous_refresh: str | None,
    ) -> OAuthCredential:
        try:
            with self._http() as http:
                response = http.post(TOKEN_URL, data=data, auth=(consumer.client_id, consumer.client_secret))
        except httpx.HTTPError as error:
            message = f"Could not reach Bitbucket's OAuth endpoint: {error}"
            raise CliError(message, exit_code=ExitCode.UNAVAILABLE) from error
        if response.status_code != httpx.codes.OK:
            raise _failure(response)
        payload: object = response.json()
        body: dict[str, object] = payload if isinstance(payload, dict) else {}
        access_token = body.get("access_token")
        if not isinstance(access_token, str) or not access_token:
            message = "Bitbucket's OAuth reply has no access token."
            raise CliError(message, exit_code=ExitCode.AUTHENTICATION)
        refresh_token = body.get("refresh_token")
        expires_in = body.get("expires_in")
        return OAuthCredential(
            client_id=consumer.client_id,
            client_secret=consumer.client_secret,
            access_token=access_token,
            grant=grant,
            refresh_token=refresh_token if isinstance(refresh_token, str) and refresh_token else previous_refresh,
            expires_at=self._clock() + float(expires_in) if isinstance(expires_in, (int, float)) else 0,
        )


# The SDK calls this on every request, so a long command keeps working across the token's lifetime:
# it renews shortly before expiry and hands the new credential back to be stored.
class OAuthTokenProvider:
    def __init__(
        self,
        credential: OAuthCredential,
        oauth: OAuthClient,
        on_renew: Callable[[OAuthCredential], None],
    ) -> None:
        self._credential = credential
        self._oauth = oauth
        self._on_renew = on_renew

    def __call__(self) -> str:
        if self._oauth.is_expired(self._credential):
            self._credential = self._oauth.renew(self._credential)
            self._on_renew(self._credential)
        return self._credential.access_token

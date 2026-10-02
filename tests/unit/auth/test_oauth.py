from __future__ import annotations

import base64
from typing import TYPE_CHECKING
from typing import Final
from urllib.parse import parse_qs
from urllib.parse import urlparse

import httpx
import pytest
import respx

from bitbucket_unofficial_cli.auth.credentials import OAuthCredential
from bitbucket_unofficial_cli.auth.credentials import OAuthGrant
from bitbucket_unofficial_cli.auth.oauth import TOKEN_URL
from bitbucket_unofficial_cli.auth.oauth import OAuthClient
from bitbucket_unofficial_cli.auth.oauth import OAuthConsumer
from bitbucket_unofficial_cli.auth.oauth import OAuthTokenProvider
from bitbucket_unofficial_cli.auth.oauth import authorize_url
from bitbucket_unofficial_cli.auth.oauth import default_http
from bitbucket_unofficial_cli.runtime.errors import CliError
from bitbucket_unofficial_cli.runtime.exit_codes import ExitCode
from tests.conftest import NOW

if TYPE_CHECKING:
    from collections.abc import Callable

CONSUMER: Final = OAuthConsumer(client_id="key", client_secret="secret")
TOKENS: Final = {"access_token": "new-access", "refresh_token": "new-refresh", "expires_in": 7200}


def stored(
    *, expires_at: float, grant: OAuthGrant = OAuthGrant.AUTHORIZATION_CODE, refresh: str | None = "old"
) -> OAuthCredential:
    return OAuthCredential(
        client_id="key",
        client_secret="secret",
        access_token="old-access",
        grant=grant,
        refresh_token=refresh,
        expires_at=expires_at,
    )


def test_authorize_url_carries_the_consumer_key_and_state() -> None:
    # Arrange
    # Act
    url = authorize_url("key", "abc")
    # Assert
    query = parse_qs(urlparse(url).query)
    assert url.startswith("https://bitbucket.org/site/oauth2/authorize?")
    assert query == {"client_id": ["key"], "response_type": ["code"], "state": ["abc"]}


def test_default_http_builds_a_client() -> None:
    # Arrange
    # Act
    with default_http() as http:
        # Assert
        assert isinstance(http, httpx.Client)


@respx.mock
def test_exchange_code_posts_the_code_with_basic_auth(oauth: OAuthClient) -> None:
    # Arrange
    route = respx.post(TOKEN_URL).mock(return_value=httpx.Response(200, json=TOKENS))
    # Act
    credential = oauth.exchange_code(CONSUMER, "the-code")
    # Assert
    request = route.calls.last.request
    assert parse_qs(request.content.decode()) == {"grant_type": ["authorization_code"], "code": ["the-code"]}
    assert request.headers["authorization"] == "Basic " + base64.b64encode(b"key:secret").decode()
    assert credential == OAuthCredential(
        client_id="key",
        client_secret="secret",
        access_token="new-access",
        grant=OAuthGrant.AUTHORIZATION_CODE,
        refresh_token="new-refresh",
        expires_at=NOW + 7200,
    )


@respx.mock
def test_client_credentials_has_no_refresh_token(oauth: OAuthClient) -> None:
    # Arrange
    respx.post(TOKEN_URL).mock(return_value=httpx.Response(200, json={"access_token": "t", "expires_in": 60}))
    # Act
    credential = oauth.client_credentials(CONSUMER)
    # Assert
    assert credential.grant is OAuthGrant.CLIENT_CREDENTIALS
    assert credential.refresh_token is None


@respx.mock
def test_a_reply_without_expiry_leaves_it_unknown(oauth: OAuthClient) -> None:
    # Arrange
    respx.post(TOKEN_URL).mock(return_value=httpx.Response(200, json={"access_token": "t"}))
    # Act
    credential = oauth.client_credentials(CONSUMER)
    # Assert
    assert credential.expires_at == 0
    assert oauth.is_expired(credential) is False


@respx.mock
def test_renew_uses_the_refresh_token_and_keeps_it_when_the_reply_omits_one(oauth: OAuthClient) -> None:
    # Arrange
    route = respx.post(TOKEN_URL).mock(return_value=httpx.Response(200, json={"access_token": "n", "expires_in": 60}))
    # Act
    renewed = oauth.renew(stored(expires_at=1))
    # Assert
    assert parse_qs(route.calls.last.request.content.decode()) == {
        "grant_type": ["refresh_token"],
        "refresh_token": ["old"],
    }
    assert renewed.access_token == "n"
    assert renewed.refresh_token == "old"


@respx.mock
def test_renew_asks_again_for_client_credentials(oauth: OAuthClient) -> None:
    # Arrange
    route = respx.post(TOKEN_URL).mock(return_value=httpx.Response(200, json=TOKENS))
    # Act
    renewed = oauth.renew(stored(expires_at=1, grant=OAuthGrant.CLIENT_CREDENTIALS, refresh=None))
    # Assert
    assert parse_qs(route.calls.last.request.content.decode()) == {"grant_type": ["client_credentials"]}
    assert renewed.access_token == "new-access"


def test_renew_without_a_refresh_token_asks_to_log_in_again(oauth: OAuthClient) -> None:
    # Arrange
    credential = stored(expires_at=1, refresh=None)
    # Act
    with pytest.raises(CliError) as caught:
        oauth.renew(credential)
    # Assert
    assert caught.value.exit_code is ExitCode.AUTHENTICATION
    assert "auth login --oauth" in (caught.value.hint or "")


@respx.mock
@pytest.mark.parametrize(
    ("response", "expected"),
    [
        (httpx.Response(400, json={"error": "invalid_grant", "error_description": "Bad code"}), "Bad code"),
        (httpx.Response(401, json={"error": "invalid_client"}), "invalid_client"),
        (httpx.Response(500, text="oops"), "HTTP 500"),
    ],
)
def test_a_rejected_request_is_an_authentication_error(
    oauth: OAuthClient, response: httpx.Response, expected: str
) -> None:
    # Arrange
    respx.post(TOKEN_URL).mock(return_value=response)
    # Act
    with pytest.raises(CliError) as caught:
        oauth.exchange_code(CONSUMER, "c")
    # Assert
    assert caught.value.exit_code is ExitCode.AUTHENTICATION
    assert expected in caught.value.message


@respx.mock
def test_a_rejected_refresh_points_to_logging_in_again(oauth: OAuthClient) -> None:
    # Arrange
    respx.post(TOKEN_URL).mock(return_value=httpx.Response(400, json={"error": "invalid_grant"}))
    # Act
    with pytest.raises(CliError) as caught:
        oauth.renew(stored(expires_at=1))
    # Assert
    assert caught.value.exit_code is ExitCode.AUTHENTICATION
    assert "auth login --oauth" in (caught.value.hint or "")


@respx.mock
def test_a_reply_without_an_access_token_is_rejected(oauth: OAuthClient) -> None:
    # Arrange
    respx.post(TOKEN_URL).mock(return_value=httpx.Response(200, json={"token_type": "bearer"}))
    # Act
    with pytest.raises(CliError) as caught:
        oauth.client_credentials(CONSUMER)
    # Assert
    assert caught.value.exit_code is ExitCode.AUTHENTICATION


@respx.mock
def test_an_unreachable_endpoint_is_unavailable(oauth: OAuthClient) -> None:
    # Arrange
    respx.post(TOKEN_URL).mock(side_effect=httpx.ConnectError("down"))
    # Act
    with pytest.raises(CliError) as caught:
        oauth.client_credentials(CONSUMER)
    # Assert
    assert caught.value.exit_code is ExitCode.UNAVAILABLE


@respx.mock
def test_a_refresh_that_cannot_reach_bitbucket_keeps_its_exit_code(oauth: OAuthClient) -> None:
    # Arrange
    respx.post(TOKEN_URL).mock(side_effect=httpx.ConnectError("down"))
    # Act
    with pytest.raises(CliError) as caught:
        oauth.renew(stored(expires_at=1))
    # Assert
    assert caught.value.exit_code is ExitCode.UNAVAILABLE


@pytest.mark.parametrize(
    ("expires_at", "expired"), [(NOW + 3600, False), (NOW + 59, True), (NOW - 1, True), (0, False)]
)
def test_is_expired_renews_a_minute_early(oauth: OAuthClient, expires_at: float, expired: bool) -> None:
    # Arrange
    credential = stored(expires_at=expires_at)
    # Act
    result = oauth.is_expired(credential)
    # Assert
    assert result is expired


def make_provider(credential: OAuthCredential, oauth: OAuthClient) -> tuple[OAuthTokenProvider, list[OAuthCredential]]:
    renewed: list[OAuthCredential] = []
    return OAuthTokenProvider(credential, oauth, renewed.append), renewed


@respx.mock
def test_provider_returns_a_fresh_token_without_calling_bitbucket(oauth: OAuthClient) -> None:
    # Arrange
    route = respx.post(TOKEN_URL)
    provider, renewed = make_provider(stored(expires_at=NOW + 3600), oauth)
    # Act
    token = provider()
    # Assert
    assert token == "old-access"
    assert not route.called
    assert renewed == []


@respx.mock
def test_provider_renews_an_expired_token_once_and_reports_it(oauth: OAuthClient) -> None:
    # Arrange
    route = respx.post(TOKEN_URL).mock(return_value=httpx.Response(200, json=TOKENS))
    provider, renewed = make_provider(stored(expires_at=NOW - 10), oauth)
    # Act
    first = provider()
    second = provider()
    # Assert
    assert (first, second) == ("new-access", "new-access")
    assert route.call_count == 1
    assert [credential.access_token for credential in renewed] == ["new-access"]


def test_the_clock_is_injectable() -> None:
    # Arrange
    ticks: list[Callable[[], float]] = [lambda: 5.0]
    oauth = OAuthClient(clock=ticks[0])
    # Act
    expired = oauth.is_expired(stored(expires_at=10))
    # Assert
    assert expired is True

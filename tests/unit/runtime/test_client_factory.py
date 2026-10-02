from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Final

import httpx
import respx
from bitbucket import NO_RETRY
from bitbucket import ClientOptions

from bitbucket_unofficial_cli.auth.credentials import AccessTokenCredential
from bitbucket_unofficial_cli.auth.credentials import ApiTokenCredential
from bitbucket_unofficial_cli.auth.credentials import OAuthCredential
from bitbucket_unofficial_cli.auth.credentials import OAuthGrant
from bitbucket_unofficial_cli.runtime.client_factory import ClientRequest
from bitbucket_unofficial_cli.runtime.client_factory import build_client
from bitbucket_unofficial_cli.runtime.client_factory import create_sdk_client
from bitbucket_unofficial_cli.runtime.client_factory import event_hooks
from tests.conftest import BASE_URL
from tests.conftest import NOW
from tests.conftest import USER_PAYLOAD

if TYPE_CHECKING:
    import pytest

    from bitbucket_unofficial_cli.auth.oauth import OAuthClient

OPTIONS: Final = ClientOptions(base_url=BASE_URL, retry=NO_RETRY)


def request(credential: object, oauth: OAuthClient) -> ClientRequest:
    return ClientRequest(credential=credential, oauth=oauth)  # type: ignore[arg-type]


@respx.mock
def test_an_api_token_is_sent_as_basic_auth(oauth: OAuthClient) -> None:
    # Arrange
    route = respx.get(f"{BASE_URL}/user").mock(return_value=httpx.Response(200, json=USER_PAYLOAD))
    # Act
    with build_client(request(ApiTokenCredential(email="a@b.c", api_token="tok"), oauth), OPTIONS) as client:
        client.user.me()
    # Assert
    assert route.calls.last.request.headers["authorization"].startswith("Basic ")


@respx.mock
def test_an_access_token_is_sent_as_a_bearer(oauth: OAuthClient) -> None:
    # Arrange
    route = respx.get(f"{BASE_URL}/user").mock(return_value=httpx.Response(200, json=USER_PAYLOAD))
    # Act
    with build_client(request(AccessTokenCredential(access_token="bearer"), oauth), OPTIONS) as client:
        client.user.me()
    # Assert
    assert route.calls.last.request.headers["authorization"] == "Bearer bearer"


@respx.mock
def test_an_oauth_credential_is_sent_as_a_bearer_through_the_provider(oauth: OAuthClient) -> None:
    # Arrange
    route = respx.get(f"{BASE_URL}/user").mock(return_value=httpx.Response(200, json=USER_PAYLOAD))
    credential = OAuthCredential(
        client_id="k",
        client_secret="s",
        access_token="oauth",
        grant=OAuthGrant.AUTHORIZATION_CODE,
        expires_at=NOW + 3600,
    )
    # Act
    with build_client(request(credential, oauth), OPTIONS) as client:
        client.user.me()
    # Assert
    assert route.calls.last.request.headers["authorization"] == "Bearer oauth"


def test_event_hooks_exist_only_when_verbose(capsys: pytest.CaptureFixture[str]) -> None:
    # Arrange
    quiet = event_hooks(verbose=False)
    loud = event_hooks(verbose=True)
    # Act
    assert loud is not None
    loud["response"][0](httpx.Response(200, request=httpx.Request("GET", "https://x.test/a")))
    loud["response"][0](object())
    # Assert
    assert quiet is None
    assert capsys.readouterr().err == "-> GET https://x.test/a 200\n-> ? ? ?\n"


def test_create_sdk_client_builds_a_real_client(oauth: OAuthClient) -> None:
    # Arrange
    token = ApiTokenCredential(email="a@b.c", api_token="tok")
    # Act
    with create_sdk_client(ClientRequest(credential=token, oauth=oauth, verbose=True)) as client:
        # Assert
        assert client is not None


def test_the_default_renew_callback_ignores_the_credential(oauth: OAuthClient) -> None:
    # Arrange
    credential = OAuthCredential(
        client_id="k", client_secret="s", access_token="a", grant=OAuthGrant.AUTHORIZATION_CODE
    )
    created = ClientRequest(credential=credential, oauth=oauth)
    # Act
    result = created.on_renew(credential)
    # Assert
    assert result is None

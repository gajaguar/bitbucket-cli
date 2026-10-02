from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Final
from urllib.parse import parse_qs
from urllib.parse import urlparse

import httpx
import pytest
import respx

from bitbucket_unofficial_cli.auth.authorization_code import AuthorizationCodeFlow
from bitbucket_unofficial_cli.auth.credentials import OAuthGrant
from bitbucket_unofficial_cli.auth.oauth import TOKEN_URL
from bitbucket_unofficial_cli.auth.oauth import OAuthConsumer
from bitbucket_unofficial_cli.runtime.errors import CliError
from bitbucket_unofficial_cli.runtime.exit_codes import ExitCode

if TYPE_CHECKING:
    from collections.abc import Callable

    from bitbucket_unofficial_cli.auth.oauth import OAuthClient
    from tests.conftest import FakeBrowser

CONSUMER: Final = OAuthConsumer(client_id="key", client_secret="secret")
TOKENS: Final = {"access_token": "access", "refresh_token": "refresh", "expires_in": 7200}


def make_flow(
    oauth: OAuthClient, browser: FakeBrowser, notes: list[str], pasted: str = "", timeout: float = 10
) -> AuthorizationCodeFlow:
    return AuthorizationCodeFlow(
        oauth=oauth,
        open_browser=browser,
        notify=notes.append,
        read_redirect=lambda: pasted,
        timeout=timeout,
    )


# Plays the user: reads the authorize URL the flow printed and pastes back the address it redirects to.
def redirect_for(notes: list[str]) -> Callable[[], str]:
    def read_redirect() -> str:
        state = parse_qs(urlparse(notes[0].splitlines()[-1]).query)["state"][0]
        return f"http://127.0.0.1:8976/callback?code=pasted&state={state}\n"

    return read_redirect


def join(browser: FakeBrowser) -> None:
    for thread in browser.threads:
        thread.join(timeout=10)


@respx.mock
def test_the_browser_flow_exchanges_the_code(oauth: OAuthClient, browser: FakeBrowser) -> None:
    # Arrange
    respx.post(TOKEN_URL).mock(return_value=httpx.Response(200, json=TOKENS))
    notes: list[str] = []
    # Act
    credential = make_flow(oauth, browser, notes).authorize(CONSUMER, port=browser.port, use_browser=True)
    join(browser)
    # Assert
    assert credential.access_token == "access"
    assert credential.grant is OAuthGrant.AUTHORIZATION_CODE
    assert parse_qs(urlparse(browser.urls[0]).query)["client_id"] == ["key"]
    assert notes == [f"Opening your browser to authorize; if it does not open, visit:\n{browser.urls[0]}"]


@respx.mock
def test_the_pasted_flow_reads_the_redirect_address(oauth: OAuthClient, browser: FakeBrowser) -> None:
    # Arrange
    respx.post(TOKEN_URL).mock(return_value=httpx.Response(200, json=TOKENS))
    notes: list[str] = []
    flow = AuthorizationCodeFlow(
        oauth=oauth, open_browser=browser, notify=notes.append, read_redirect=redirect_for(notes)
    )
    # Act
    credential = flow.authorize(CONSUMER, port=browser.port, use_browser=False)
    # Assert
    assert credential.access_token == "access"
    assert browser.urls == []


def test_a_state_mismatch_is_rejected(oauth: OAuthClient, browser: FakeBrowser) -> None:
    # Arrange
    browser.state = "forged"
    # Act
    with pytest.raises(CliError) as caught:
        make_flow(oauth, browser, []).authorize(CONSUMER, port=browser.port, use_browser=True)
    join(browser)
    # Assert
    assert caught.value.exit_code is ExitCode.AUTHENTICATION
    assert "state mismatch" in caught.value.message


def test_a_denied_authorization_reports_the_reason(oauth: OAuthClient, browser: FakeBrowser) -> None:
    # Arrange
    browser.code = None
    browser.error = "access_denied"
    # Act
    with pytest.raises(CliError) as caught:
        make_flow(oauth, browser, []).authorize(CONSUMER, port=browser.port, use_browser=True)
    join(browser)
    # Assert
    assert "access_denied" in caught.value.message


def test_a_reply_without_a_code_is_rejected(oauth: OAuthClient, browser: FakeBrowser) -> None:
    # Arrange
    browser.code = None
    # Act
    with pytest.raises(CliError) as caught:
        make_flow(oauth, browser, []).authorize(CONSUMER, port=browser.port, use_browser=True)
    join(browser)
    # Assert
    assert "no code" in caught.value.message


def test_a_browser_that_never_returns_times_out(oauth: OAuthClient, browser: FakeBrowser) -> None:
    # Arrange
    browser.silent = True
    # Act
    with pytest.raises(CliError) as caught:
        make_flow(oauth, browser, [], timeout=0.05).authorize(CONSUMER, port=browser.port, use_browser=True)
    # Assert
    assert caught.value.exit_code is ExitCode.AUTHENTICATION

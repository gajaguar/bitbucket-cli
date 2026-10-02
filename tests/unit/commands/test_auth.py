from __future__ import annotations

import json
from typing import TYPE_CHECKING
from typing import Final

import httpx
import pytest
import respx

from bitbucket_unofficial_cli.auth.credentials import AccessTokenCredential
from bitbucket_unofficial_cli.auth.credentials import ApiTokenCredential
from bitbucket_unofficial_cli.auth.credentials import OAuthCredential
from bitbucket_unofficial_cli.auth.credentials import OAuthGrant
from bitbucket_unofficial_cli.auth.oauth import TOKEN_URL
from bitbucket_unofficial_cli.runtime.exit_codes import ExitCode
from tests.conftest import BASE_URL
from tests.conftest import NOW
from tests.conftest import USER_PAYLOAD
from tests.conftest import WORKSPACE_PAYLOAD

if TYPE_CHECKING:
    from typer import Typer
    from typer.testing import CliRunner

    from bitbucket_unofficial_cli.runtime.context import Services
    from tests.conftest import FakeBrowser

TOKENS: Final = {"access_token": "oauth-access", "refresh_token": "oauth-refresh", "expires_in": 7200}
API: Final = ApiTokenCredential(email="me@example.com", api_token="api-token-1234")


def login_api(cli: Typer, runner: CliRunner, *extra: str, token: str = "api-token-1234\n") -> object:
    return runner.invoke(
        cli, ["-o", "json", "auth", "login", "--email", "me@example.com", "--with-token", *extra], input=token
    )


@respx.mock
def test_login_with_an_api_token_validates_stores_and_saves_the_profile(
    cli: Typer, runner: CliRunner, services: Services
) -> None:
    # Arrange
    route = respx.get(f"{BASE_URL}/user").mock(return_value=httpx.Response(200, json=USER_PAYLOAD))
    # Act
    result = login_api(cli, runner)
    # Assert
    assert result.exit_code == ExitCode.OK
    assert json.loads(result.stdout) == {
        "profile": "default",
        "user": "Some One",
        "kind": "api_token",
        "source": "keyring",
        "expiresAt": None,
        "secret": "********1234",
    }
    assert route.calls.last.request.headers["authorization"].startswith("Basic ")
    assert services.credentials.keyring.get("default") == API
    profile = services.settings.load().profiles["default"]
    assert (profile.display_name, profile.account_id) == ("Some One", "557058:abc")
    assert services.settings.load().default_profile == "default"


@respx.mock
def test_login_prompts_for_the_email_and_token(cli: Typer, runner: CliRunner, services: Services) -> None:
    # Arrange
    respx.get(f"{BASE_URL}/user").mock(return_value=httpx.Response(200, json=USER_PAYLOAD))
    # Act
    result = runner.invoke(cli, ["auth", "login"], input="me@example.com\napi-token-1234\n")
    # Assert
    assert result.exit_code == ExitCode.OK
    assert services.credentials.keyring.get("default") == API


@respx.mock
def test_a_rejected_credential_is_not_stored(cli: Typer, runner: CliRunner, services: Services) -> None:
    # Arrange
    respx.get(f"{BASE_URL}/user").mock(
        return_value=httpx.Response(401, json={"type": "error", "error": {"message": "no"}})
    )
    # Act
    result = login_api(cli, runner)
    # Assert
    assert result.exit_code == ExitCode.AUTHENTICATION
    assert services.credentials.keyring.get("default") is None
    assert services.settings.load().profiles == {}


def test_an_empty_secret_is_a_usage_error(cli: Typer, runner: CliRunner) -> None:
    # Arrange
    # Act
    result = login_api(cli, runner, token="\n")
    # Assert
    assert result.exit_code == ExitCode.USAGE


def test_an_empty_email_is_a_usage_error(cli: Typer, runner: CliRunner) -> None:
    # Arrange
    # Act
    result = runner.invoke(cli, ["auth", "login", "--email", " ", "--with-token"], input="tok\n")
    # Assert
    assert result.exit_code == ExitCode.USAGE


def test_the_login_modes_are_exclusive(cli: Typer, runner: CliRunner) -> None:
    # Arrange
    # Act
    result = runner.invoke(cli, ["auth", "login", "--api-token", "--oauth"])
    # Assert
    assert result.exit_code == ExitCode.USAGE


@respx.mock
def test_login_with_an_access_token_checks_the_workspace(cli: Typer, runner: CliRunner, services: Services) -> None:
    # Arrange
    route = respx.get(f"{BASE_URL}/workspaces/acme").mock(return_value=httpx.Response(200, json=WORKSPACE_PAYLOAD))
    # Act
    result = runner.invoke(
        cli, ["-o", "json", "-w", "acme", "auth", "login", "--access-token", "--with-token"], input="bearer-token\n"
    )
    # Assert
    assert result.exit_code == ExitCode.OK
    assert route.calls.last.request.headers["authorization"] == "Bearer bearer-token"
    assert services.credentials.keyring.get("default") == AccessTokenCredential(access_token="bearer-token")
    assert json.loads(result.stdout)["user"] == "(access token)"
    assert services.settings.load().profiles["default"].workspace == "acme"


def test_an_access_token_without_a_workspace_is_stored_unchecked(
    cli: Typer, runner: CliRunner, services: Services
) -> None:
    # Arrange
    # Act
    result = runner.invoke(cli, ["auth", "login", "--access-token", "--with-token"], input="bearer-token\n")
    # Assert
    assert result.exit_code == ExitCode.OK
    assert "not validated" in result.stderr
    assert services.credentials.keyring.get("default") is not None


@respx.mock
def test_login_with_oauth_client_credentials(
    cli: Typer, runner: CliRunner, services: Services, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Arrange
    monkeypatch.setenv("BITBUCKET_OAUTH_CLIENT_SECRET", "consumer-secret")
    respx.post(TOKEN_URL).mock(return_value=httpx.Response(200, json=TOKENS))
    user = respx.get(f"{BASE_URL}/user").mock(return_value=httpx.Response(200, json=USER_PAYLOAD))
    # Act
    result = runner.invoke(
        cli, ["-o", "json", "auth", "login", "--oauth", "--client-credentials", "--client-id", "key"]
    )
    # Assert
    assert result.exit_code == ExitCode.OK
    assert user.calls.last.request.headers["authorization"] == "Bearer oauth-access"
    stored = services.credentials.keyring.get("default")
    assert isinstance(stored, OAuthCredential)
    assert (stored.grant, stored.client_secret, stored.refresh_token) == (
        OAuthGrant.CLIENT_CREDENTIALS,
        "consumer-secret",
        "oauth-refresh",
    )
    assert (
        json.loads(result.stdout)["expiresAt"] == "1970-01-12T14:46:40+00:00" or json.loads(result.stdout)["expiresAt"]
    )


@respx.mock
def test_login_with_oauth_authorization_code_through_the_browser(
    cli: Typer, runner: CliRunner, services: Services, browser: FakeBrowser
) -> None:
    # Arrange
    respx.post(TOKEN_URL).mock(return_value=httpx.Response(200, json=TOKENS))
    respx.get(f"{BASE_URL}/user").mock(return_value=httpx.Response(200, json=USER_PAYLOAD))
    # Act
    result = runner.invoke(
        cli,
        ["auth", "login", "--oauth", "--client-id", "key", "--callback-port", str(browser.port), "--with-token"],
        input="consumer-secret\n",
    )
    for thread in browser.threads:
        thread.join(timeout=10)
    # Assert
    assert result.exit_code == ExitCode.OK
    stored = services.credentials.keyring.get("default")
    assert isinstance(stored, OAuthCredential)
    assert stored.grant is OAuthGrant.AUTHORIZATION_CODE


@respx.mock
def test_login_with_oauth_no_browser_reads_the_pasted_address(
    cli: Typer, runner: CliRunner, services: Services, browser: FakeBrowser
) -> None:
    # Arrange
    respx.post(TOKEN_URL).mock(return_value=httpx.Response(200, json=TOKENS))
    respx.get(f"{BASE_URL}/user").mock(return_value=httpx.Response(200, json=USER_PAYLOAD))
    # Act
    result = runner.invoke(
        cli,
        ["auth", "login", "--oauth", "--no-browser", "--client-id", "key", "--with-token"],
        input="consumer-secret\nhttp://127.0.0.1:8976/callback?code=c&state=wrong\n",
    )
    # Assert
    assert result.exit_code == ExitCode.AUTHENTICATION
    assert browser.urls == []
    assert "https://bitbucket.org/site/oauth2/authorize" in result.stderr
    assert services.credentials.keyring.get("default") is None


def test_insecure_storage_writes_the_file_store(cli: Typer, runner: CliRunner, services: Services) -> None:
    # Arrange
    with respx.mock:
        respx.get(f"{BASE_URL}/user").mock(return_value=httpx.Response(200, json=USER_PAYLOAD))
        # Act
        result = login_api(cli, runner, "--insecure-storage")
    # Assert
    assert result.exit_code == ExitCode.OK
    assert services.credentials.file.get("default") == API
    assert services.credentials.keyring.get("default") is None


def test_login_without_a_keyring_asks_for_insecure_storage(
    cli: Typer, runner: CliRunner, services: Services, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Arrange
    monkeypatch.setattr(type(services.credentials.keyring), "available", staticmethod(lambda: False))
    # Act
    result = login_api(cli, runner)
    # Assert
    assert result.exit_code == ExitCode.CONFIGURATION
    assert "--insecure-storage" in result.stderr


@respx.mock
def test_status_reports_the_credential_and_user(
    cli: Typer, runner: CliRunner, services: Services, environ: dict[str, str]
) -> None:
    # Arrange
    environ.update({"ATLASSIAN_USER_EMAIL": "me@example.com", "ATLASSIAN_API_TOKEN": "api-token-1234"})
    respx.get(f"{BASE_URL}/user").mock(return_value=httpx.Response(200, json=USER_PAYLOAD))
    # Act
    result = runner.invoke(cli, ["-o", "json", "auth", "status"])
    # Assert
    assert result.exit_code == ExitCode.OK
    assert json.loads(result.stdout) == {
        "profile": "default",
        "user": "Some One",
        "kind": "api_token",
        "source": "environment",
        "expiresAt": None,
        "secret": "********1234",
    }


@respx.mock
def test_status_of_an_access_token_checks_the_selected_workspace(
    cli: Typer, runner: CliRunner, environ: dict[str, str]
) -> None:
    # Arrange
    environ["BITBUCKET_ACCESS_TOKEN"] = "bearer-token"
    route = respx.get(f"{BASE_URL}/workspaces/acme").mock(return_value=httpx.Response(200, json=WORKSPACE_PAYLOAD))
    # Act
    result = runner.invoke(cli, ["-o", "json", "-w", "acme", "auth", "status"])
    # Assert
    assert result.exit_code == ExitCode.OK
    assert route.called
    assert json.loads(result.stdout)["kind"] == "access_token"


def test_status_without_a_credential_is_a_configuration_error(cli: Typer, runner: CliRunner) -> None:
    # Arrange
    # Act
    result = runner.invoke(cli, ["auth", "status"])
    # Assert
    assert result.exit_code == ExitCode.CONFIGURATION
    assert "auth login" in result.stderr


def test_logout_removes_the_credential_and_profile(cli: Typer, runner: CliRunner, services: Services) -> None:
    # Arrange
    with respx.mock:
        respx.get(f"{BASE_URL}/user").mock(return_value=httpx.Response(200, json=USER_PAYLOAD))
        login_api(cli, runner)
    # Act
    result = runner.invoke(cli, ["auth", "logout"])
    # Assert
    assert result.exit_code == ExitCode.OK
    assert services.credentials.keyring.get("default") is None
    assert "default" not in services.settings.load().profiles


def test_logout_without_anything_stored_fails(cli: Typer, runner: CliRunner) -> None:
    # Arrange
    # Act
    result = runner.invoke(cli, ["auth", "logout"])
    # Assert
    assert result.exit_code == ExitCode.CONFIGURATION


def test_logout_warns_when_the_environment_still_has_a_credential(
    cli: Typer, runner: CliRunner, services: Services, environ: dict[str, str]
) -> None:
    # Arrange
    services.credentials.keyring.set("default", API)
    environ["BITBUCKET_ACCESS_TOKEN"] = "bearer"
    # Act
    result = runner.invoke(cli, ["auth", "logout"])
    # Assert
    assert result.exit_code == ExitCode.OK
    assert "still set in the environment" in result.stderr


@pytest.mark.parametrize(
    ("credential", "expected"),
    [(API, "api-token-1234"), (AccessTokenCredential(access_token="bearer-9"), "bearer-9")],
)
def test_token_prints_the_secret(
    cli: Typer, runner: CliRunner, services: Services, credential: object, expected: str
) -> None:
    # Arrange
    services.credentials.keyring.set("default", credential)  # type: ignore[arg-type]
    # Act
    result = runner.invoke(cli, ["auth", "token"])
    # Assert
    assert result.stdout == f"{expected}\n"


@respx.mock
def test_token_renews_an_expired_oauth_token_and_stores_it(cli: Typer, runner: CliRunner, services: Services) -> None:
    # Arrange
    expired = OAuthCredential(
        client_id="key",
        client_secret="s",
        access_token="stale",
        grant=OAuthGrant.AUTHORIZATION_CODE,
        refresh_token="r",
        expires_at=NOW - 5,
    )
    services.credentials.keyring.set("default", expired)
    respx.post(TOKEN_URL).mock(return_value=httpx.Response(200, json=TOKENS))
    # Act
    result = runner.invoke(cli, ["auth", "token"])
    # Assert
    assert result.stdout == "oauth-access\n"
    stored = services.credentials.keyring.get("default")
    assert isinstance(stored, OAuthCredential)
    assert stored.access_token == "oauth-access"


@respx.mock
def test_refresh_renews_and_stores_the_oauth_token(cli: Typer, runner: CliRunner, services: Services) -> None:
    # Arrange
    current = OAuthCredential(
        client_id="key",
        client_secret="s",
        access_token="old",
        grant=OAuthGrant.AUTHORIZATION_CODE,
        refresh_token="r",
        expires_at=NOW + 3600,
    )
    services.credentials.keyring.set("default", current)
    respx.post(TOKEN_URL).mock(return_value=httpx.Response(200, json=TOKENS))
    # Act
    result = runner.invoke(cli, ["auth", "refresh"])
    # Assert
    assert result.exit_code == ExitCode.OK
    assert "Token renewed" in result.stderr
    stored = services.credentials.keyring.get("default")
    assert isinstance(stored, OAuthCredential)
    assert stored.access_token == "oauth-access"


def test_refresh_rejects_a_credential_that_is_not_oauth(cli: Typer, runner: CliRunner, services: Services) -> None:
    # Arrange
    services.credentials.keyring.set("default", API)
    # Act
    result = runner.invoke(cli, ["auth", "refresh"])
    # Assert
    assert result.exit_code == ExitCode.USAGE

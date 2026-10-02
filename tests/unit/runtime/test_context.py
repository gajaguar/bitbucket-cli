from __future__ import annotations

import json
from typing import TYPE_CHECKING
from typing import Final

import httpx
import respx
import typer

from bitbucket_unofficial_cli.auth.credentials import OAuthCredential
from bitbucket_unofficial_cli.auth.credentials import OAuthGrant
from bitbucket_unofficial_cli.auth.oauth import TOKEN_URL
from bitbucket_unofficial_cli.runtime.context import get_app_context
from bitbucket_unofficial_cli.runtime.errors import CliError
from bitbucket_unofficial_cli.runtime.exit_codes import ExitCode
from tests.conftest import BASE_URL
from tests.conftest import NOW
from tests.conftest import USER_PAYLOAD

if TYPE_CHECKING:
    from typer.testing import CliRunner

    from bitbucket_unofficial_cli.runtime.context import Services


PROBE: Final = typer.Typer()


@PROBE.command()
def check(ctx: typer.Context) -> None:
    get_app_context(ctx)


def test_get_app_context_needs_an_initialized_root(runner: CliRunner) -> None:
    # Arrange
    # Act
    result = runner.invoke(PROBE, [])
    # Assert
    assert isinstance(result.exception, CliError)
    assert "not initialized" in result.exception.message


@respx.mock
def test_a_token_renewed_mid_command_is_stored_where_it_came_from(
    cli: typer.Typer, runner: CliRunner, services: Services
) -> None:
    # Arrange
    stale = OAuthCredential(
        client_id="key",
        client_secret="s",
        access_token="stale",
        grant=OAuthGrant.AUTHORIZATION_CODE,
        refresh_token="r",
        expires_at=NOW - 5,
    )
    services.credentials.file.set("default", stale)
    respx.post(TOKEN_URL).mock(
        return_value=httpx.Response(200, json={"access_token": "fresh", "refresh_token": "r2", "expires_in": 7200})
    )
    user = respx.get(f"{BASE_URL}/user").mock(return_value=httpx.Response(200, json=USER_PAYLOAD))
    # Act
    result = runner.invoke(cli, ["-o", "json", "user", "me"])
    # Assert
    assert result.exit_code == ExitCode.OK
    assert json.loads(result.stdout)["display_name"] == "Some One"
    assert user.calls.last.request.headers["authorization"] == "Bearer fresh"
    stored = services.credentials.file.get("default")
    assert isinstance(stored, OAuthCredential)
    assert (stored.access_token, stored.refresh_token) == ("fresh", "r2")

from __future__ import annotations

import pytest
import typer
from bitbucket.errors import AuthenticationError
from bitbucket.errors import BitbucketAPIError
from bitbucket.errors import BitbucketError
from bitbucket.errors import ConfigurationError
from bitbucket.errors import ConflictError
from bitbucket.errors import ErrorBody
from bitbucket.errors import ForbiddenError
from bitbucket.errors import MissingCredentialsError
from bitbucket.errors import NotFoundError
from bitbucket.errors import PollTimeoutError
from bitbucket.errors import RateLimitError
from bitbucket.errors import ServerError
from bitbucket.errors import TransportError
from bitbucket.errors import ValidationError

from bitbucket_unofficial_cli.runtime.errors import CliError
from bitbucket_unofficial_cli.runtime.errors import describe
from bitbucket_unofficial_cli.runtime.errors import exit_code_for
from bitbucket_unofficial_cli.runtime.errors import handle_errors
from bitbucket_unofficial_cli.runtime.exit_codes import ExitCode


def api_error(kind: type[BitbucketAPIError], status: int) -> BitbucketAPIError:
    return kind(status, body=ErrorBody(message="boom"))


@pytest.mark.parametrize(
    ("error", "expected"),
    [
        (ConfigurationError("x"), ExitCode.CONFIGURATION),
        (MissingCredentialsError("x"), ExitCode.CONFIGURATION),
        (api_error(AuthenticationError, 401), ExitCode.AUTHENTICATION),
        (api_error(ForbiddenError, 403), ExitCode.FORBIDDEN),
        (api_error(NotFoundError, 404), ExitCode.NOT_FOUND),
        (api_error(ValidationError, 400), ExitCode.VALIDATION),
        (api_error(ConflictError, 409), ExitCode.VALIDATION),
        (api_error(RateLimitError, 429), ExitCode.RATE_LIMITED),
        (api_error(ServerError, 503), ExitCode.UNAVAILABLE),
        (TransportError("x"), ExitCode.UNAVAILABLE),
        (PollTimeoutError("x"), ExitCode.UNAVAILABLE),
        (BitbucketError("x"), ExitCode.FAILURE),
    ],
)
def test_sdk_errors_map_to_frozen_exit_codes(error: BitbucketError, expected: ExitCode) -> None:
    # Arrange
    # Act
    code = exit_code_for(error)
    # Assert
    assert code is expected


def test_the_exit_code_values_are_stable() -> None:
    # Arrange
    # Act
    values = {code.name: int(code) for code in ExitCode}
    # Assert
    assert values == {
        "OK": 0,
        "FAILURE": 1,
        "USAGE": 2,
        "CONFIGURATION": 3,
        "AUTHENTICATION": 4,
        "FORBIDDEN": 5,
        "NOT_FOUND": 6,
        "VALIDATION": 7,
        "RATE_LIMITED": 8,
        "UNAVAILABLE": 9,
    }


def test_describe_adds_the_http_status_and_falls_back_to_the_type_name() -> None:
    # Arrange
    # Act
    # Assert
    assert describe(api_error(NotFoundError, 404)) == "boom (HTTP 404)"
    assert describe(BitbucketError()) == "BitbucketError"


@handle_errors
def fail_cli() -> None:
    message = "bad [input]"
    raise CliError(message, exit_code=ExitCode.USAGE, hint="try again")


@handle_errors
def fail_sdk() -> None:
    raise api_error(AuthenticationError, 401)


def test_handle_errors_turns_failures_into_exit_codes(capsys: pytest.CaptureFixture[str]) -> None:
    # Arrange
    # Act
    with pytest.raises(typer.Exit) as cli_exit:
        fail_cli()
    with pytest.raises(typer.Exit) as sdk_exit:
        fail_sdk()
    # Assert
    assert cli_exit.value.exit_code == ExitCode.USAGE
    assert sdk_exit.value.exit_code == ExitCode.AUTHENTICATION
    err = capsys.readouterr().err
    assert "bad [input]" in err
    assert "try again" in err
    assert "auth login" in err

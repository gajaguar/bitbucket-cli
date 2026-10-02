from __future__ import annotations

import threading
import urllib.error
import urllib.request

import pytest

from bitbucket_unofficial_cli.auth.callback_server import CallbackResult
from bitbucket_unofficial_cli.auth.callback_server import CallbackServer
from bitbucket_unofficial_cli.auth.callback_server import parse_redirect
from bitbucket_unofficial_cli.runtime.errors import CliError
from bitbucket_unofficial_cli.runtime.exit_codes import ExitCode


def get(url: str) -> int:
    try:
        with urllib.request.urlopen(url, timeout=10) as response:  # ruff: ignore[suspicious-url-open-usage]
            return int(response.status)
    except urllib.error.HTTPError as error:
        return error.code


def visit_two_paths(port: int, statuses: list[int]) -> None:
    statuses.extend((
        get(f"http://127.0.0.1:{port}/favicon.ico"),
        get(f"http://127.0.0.1:{port}/callback?code=c&state=s"),
    ))


def test_parse_redirect_reads_code_state_and_error() -> None:
    # Arrange
    # Act
    ok = parse_redirect("http://127.0.0.1:8976/callback?code=c&state=s")
    denied = parse_redirect("/callback?error=access_denied&error_description=No+way&state=s")
    empty = parse_redirect("http://127.0.0.1:8976/callback")
    # Assert
    assert ok == CallbackResult(code="c", state="s")
    assert denied == CallbackResult(state="s", error="No way")
    assert empty == CallbackResult()


def test_the_server_returns_the_callback_query() -> None:
    # Arrange
    server = CallbackServer(0)
    statuses: list[int] = []
    thread = threading.Thread(
        target=lambda: statuses.append(get(f"http://127.0.0.1:{server.port}/callback?code=c&state=s"))
    )
    thread.start()
    # Act
    try:
        result = server.wait(10)
    finally:
        server.close()
    thread.join()
    # Assert
    assert result == CallbackResult(code="c", state="s")
    assert statuses == [200]


def test_other_paths_are_ignored_until_the_callback_arrives() -> None:
    # Arrange
    server = CallbackServer(0)
    statuses: list[int] = []
    thread = threading.Thread(target=visit_two_paths, args=(server.port, statuses))
    thread.start()
    # Act
    try:
        result = server.wait(10)
    finally:
        server.close()
    thread.join()
    # Assert
    assert result.code == "c"
    assert statuses == [404, 200]


def test_waiting_times_out_with_an_authentication_error() -> None:
    # Arrange
    server = CallbackServer(0)
    # Act
    try:
        with pytest.raises(CliError) as caught:
            server.wait(0.05)
    finally:
        server.close()
    # Assert
    assert caught.value.exit_code is ExitCode.AUTHENTICATION


def test_a_busy_port_is_a_configuration_error() -> None:
    # Arrange
    first = CallbackServer(0)
    # Act
    try:
        with pytest.raises(CliError) as caught:
            CallbackServer(first.port)
    finally:
        first.close()
    # Assert
    assert caught.value.exit_code is ExitCode.CONFIGURATION
    assert "--callback-port" in (caught.value.hint or "")

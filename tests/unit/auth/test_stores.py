from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Final

import pytest

from bitbucket_unofficial_cli.auth.credentials import AccessTokenCredential
from bitbucket_unofficial_cli.auth.credentials import ApiTokenCredential
from bitbucket_unofficial_cli.auth.credentials import CredentialSource
from bitbucket_unofficial_cli.auth.env_store import EnvCredentialStore
from bitbucket_unofficial_cli.auth.file_store import FileCredentialStore
from bitbucket_unofficial_cli.auth.keyring_store import KeyringCredentialStore
from bitbucket_unofficial_cli.runtime.errors import CliError
from bitbucket_unofficial_cli.runtime.exit_codes import ExitCode

if TYPE_CHECKING:
    from pathlib import Path

    from tests.conftest import MemoryKeyring

API: Final = ApiTokenCredential(email="a@b.c", api_token="tok")
ACCESS: Final = AccessTokenCredential(access_token="bearer")


def test_env_store_reads_an_api_token() -> None:
    # Arrange
    store = EnvCredentialStore({"ATLASSIAN_USER_EMAIL": "a@b.c", "ATLASSIAN_API_TOKEN": "tok"})
    # Act
    credential = store.get("any")
    # Assert
    assert credential == API
    assert store.source is CredentialSource.ENVIRONMENT


def test_env_store_reads_an_access_token() -> None:
    # Arrange
    store = EnvCredentialStore({"BITBUCKET_ACCESS_TOKEN": "bearer"})
    # Act
    credential = store.get("any")
    # Assert
    assert credential == ACCESS


@pytest.mark.parametrize("environ", [{}, {"ATLASSIAN_API_TOKEN": "tok"}, {"ATLASSIAN_USER_EMAIL": "a@b.c"}])
def test_env_store_needs_a_complete_credential(environ: dict[str, str]) -> None:
    # Arrange
    store = EnvCredentialStore(environ)
    # Act
    credential = store.get("any")
    # Assert
    assert credential is None


def test_env_store_refuses_both_kinds_at_once() -> None:
    # Arrange
    environ = {"ATLASSIAN_USER_EMAIL": "a@b.c", "ATLASSIAN_API_TOKEN": "tok", "BITBUCKET_ACCESS_TOKEN": "bearer"}
    store = EnvCredentialStore(environ)
    # Act
    with pytest.raises(CliError) as caught:
        store.get("any")
    # Assert
    assert caught.value.exit_code is ExitCode.CONFIGURATION


def test_keyring_store_round_trip(memory_keyring: MemoryKeyring) -> None:
    # Arrange
    store = KeyringCredentialStore()
    # Act
    store.set("work", API)
    # Assert
    assert memory_keyring.passwords["bitbucket-cli", "work"]
    assert store.get("work") == API
    assert store.delete("work") is True
    assert store.get("work") is None
    assert store.delete("work") is False


def test_file_store_round_trip(tmp_path: Path) -> None:
    # Arrange
    store = FileCredentialStore(tmp_path / "credentials.toml")
    # Act
    store.set("work", ACCESS)
    # Assert
    assert store.get("work") == ACCESS
    assert (tmp_path / "credentials.toml").stat().st_mode & 0o777 == 0o600
    assert store.delete("work") is True
    assert store.delete("work") is False
    assert store.get("work") is None

from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Final

import keyring
import pytest
from keyring.backends.fail import Keyring as FailKeyring
from keyring.errors import KeyringError

from bitbucket_unofficial_cli.auth.credentials import ApiTokenCredential
from bitbucket_unofficial_cli.auth.credentials import CredentialSource
from bitbucket_unofficial_cli.auth.file_store import FileCredentialStore
from bitbucket_unofficial_cli.auth.keyring_store import KeyringCredentialStore
from bitbucket_unofficial_cli.runtime.errors import CliError
from bitbucket_unofficial_cli.runtime.exit_codes import ExitCode

if TYPE_CHECKING:
    from pathlib import Path

API: Final = ApiTokenCredential(email="a@b.c", api_token="tok")


@pytest.fixture(name="broken_keyring")
def broken_keyring_fixture() -> object:
    previous = keyring.get_keyring()
    keyring.set_keyring(FailKeyring())
    yield None
    keyring.set_keyring(previous)


@pytest.mark.usefixtures("broken_keyring")
def test_without_a_backend_the_keyring_store_is_unavailable_and_empty() -> None:
    # Arrange
    store = KeyringCredentialStore()
    # Act
    # Assert
    assert store.available() is False
    assert store.get("work") is None
    assert store.delete("work") is False
    assert store.source is CredentialSource.KEYRING


@pytest.mark.usefixtures("broken_keyring")
def test_writing_to_a_broken_keyring_suggests_insecure_storage() -> None:
    # Arrange
    store = KeyringCredentialStore()
    # Act
    with pytest.raises(CliError) as caught:
        store.set("work", API)
    # Assert
    assert caught.value.exit_code is ExitCode.CONFIGURATION
    assert "--insecure-storage" in (caught.value.hint or "")


def failing_get_password(service: str, username: str) -> str:
    raise KeyringError(service + username)


def test_reading_a_failing_keyring_yields_nothing(monkeypatch: pytest.MonkeyPatch, memory_keyring: object) -> None:
    # Arrange
    del memory_keyring
    monkeypatch.setattr(keyring, "get_password", failing_get_password)
    # Act
    credential = KeyringCredentialStore().get("work")
    # Assert
    assert credential is None


def test_the_file_store_ignores_a_malformed_profiles_table(tmp_path: Path) -> None:
    # Arrange
    path = tmp_path / "credentials.toml"
    path.write_text('profiles = "oops"')
    store = FileCredentialStore(path)
    # Act
    credential = store.get("work")
    # Assert
    assert credential is None
    assert store.source is CredentialSource.FILE
    assert store.available() is True

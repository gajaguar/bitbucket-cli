from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Final

import keyring
from keyring.backends.fail import Keyring as FailKeyring
from keyring.errors import KeyringError
from keyring.errors import PasswordDeleteError

from bitbucket_unofficial_cli.auth.credentials import CredentialSource
from bitbucket_unofficial_cli.auth.credentials import decode
from bitbucket_unofficial_cli.auth.credentials import encode
from bitbucket_unofficial_cli.runtime.errors import CliError
from bitbucket_unofficial_cli.runtime.exit_codes import ExitCode

if TYPE_CHECKING:
    from bitbucket_unofficial_cli.auth.credentials import Credential

SERVICE_NAME: Final = "bitbucket-cli"


class KeyringCredentialStore:
    def __init__(self, service: str = SERVICE_NAME) -> None:
        self._service = service

    @property
    def source(self) -> CredentialSource:
        return CredentialSource.KEYRING

    @staticmethod
    def available() -> bool:
        return not isinstance(keyring.get_keyring(), FailKeyring)

    def get(self, profile: str) -> Credential | None:
        if not self.available():
            return None
        try:
            raw = keyring.get_password(self._service, profile)
        except KeyringError:
            return None
        return decode(raw) if raw else None

    def set(self, profile: str, credential: Credential) -> None:
        try:
            keyring.set_password(self._service, profile, encode(credential))
        except KeyringError as error:
            message = f"Could not write to the system keyring: {error}"
            raise CliError(
                message,
                exit_code=ExitCode.CONFIGURATION,
                hint="Retry with --insecure-storage to use a 0600 file instead.",
            ) from error

    def delete(self, profile: str) -> bool:
        if not self.available():
            return False
        try:
            keyring.delete_password(self._service, profile)
        except PasswordDeleteError:
            return False
        return True

from __future__ import annotations

from typing import TYPE_CHECKING

from bitbucket_unofficial_cli.auth.credentials import CredentialSource
from bitbucket_unofficial_cli.auth.credentials import decode
from bitbucket_unofficial_cli.auth.credentials import encode
from bitbucket_unofficial_cli.config.store import read_toml
from bitbucket_unofficial_cli.config.store import write_private_toml

if TYPE_CHECKING:
    from pathlib import Path

    from bitbucket_unofficial_cli.auth.credentials import Credential


# Plaintext fallback for hosts without a keyring backend; only written on explicit opt-in.
class FileCredentialStore:
    def __init__(self, path: Path) -> None:
        self.path = path

    @property
    def source(self) -> CredentialSource:
        return CredentialSource.FILE

    @staticmethod
    def available() -> bool:
        return True

    def get(self, profile: str) -> Credential | None:
        raw = self._entries().get(profile)
        return decode(raw) if isinstance(raw, str) else None

    def set(self, profile: str, credential: Credential) -> None:
        entries = self._entries()
        entries[profile] = encode(credential)
        write_private_toml(self.path, {"profiles": entries})

    def delete(self, profile: str) -> bool:
        entries = self._entries()
        if profile not in entries:
            return False
        del entries[profile]
        write_private_toml(self.path, {"profiles": entries})
        return True

    def _entries(self) -> dict[str, object]:
        profiles = read_toml(self.path).get("profiles")
        return dict(profiles) if isinstance(profiles, dict) else {}

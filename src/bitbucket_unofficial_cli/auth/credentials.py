from __future__ import annotations

import json
from dataclasses import asdict
from dataclasses import dataclass
from enum import StrEnum
from typing import Final
from typing import Literal
from typing import Protocol

_VISIBLE_SUFFIX: Final = 4


class CredentialSource(StrEnum):
    ENVIRONMENT = "environment"
    KEYRING = "keyring"
    FILE = "file"


class OAuthGrant(StrEnum):
    AUTHORIZATION_CODE = "authorization_code"
    CLIENT_CREDENTIALS = "client_credentials"


def mask(secret: str) -> str:
    if len(secret) <= _VISIBLE_SUFFIX:
        return "*" * len(secret)
    return "*" * 8 + secret[-_VISIBLE_SUFFIX:]


# Atlassian API token, sent with the account email as HTTP Basic.
@dataclass(frozen=True, slots=True)
class ApiTokenCredential:
    email: str
    api_token: str
    kind: Literal["api_token"] = "api_token"

    def masked(self) -> str:
        return mask(self.api_token)


# Any ready-made bearer: a repository, project or workspace access token, or a token
# obtained elsewhere. It is sent as-is and never refreshed.
@dataclass(frozen=True, slots=True)
class AccessTokenCredential:
    access_token: str
    kind: Literal["access_token"] = "access_token"

    def masked(self) -> str:
        return mask(self.access_token)


# An OAuth consumer's token. The client secret is kept so the token can be renewed without
# asking again; `expires_at` is epoch seconds, and 0 means the expiry is unknown.
@dataclass(frozen=True, slots=True)
class OAuthCredential:
    client_id: str
    client_secret: str
    access_token: str
    grant: OAuthGrant
    refresh_token: str | None = None
    expires_at: float = 0
    kind: Literal["oauth"] = "oauth"

    def masked(self) -> str:
        return mask(self.access_token)


type Credential = ApiTokenCredential | AccessTokenCredential | OAuthCredential  # pylint: disable=gajaguar-module-const-naming


@dataclass(frozen=True, slots=True)
class ResolvedCredential:
    credential: Credential
    source: CredentialSource


def encode(credential: Credential) -> str:
    return json.dumps(asdict(credential))


def _text(payload: dict[str, object], key: str) -> str | None:
    value = payload.get(key)
    return value if isinstance(value, str) and value else None


def _decode_oauth(payload: dict[str, object]) -> OAuthCredential | None:
    client_id = _text(payload, "client_id")
    client_secret = _text(payload, "client_secret")
    access_token = _text(payload, "access_token")
    grant = _text(payload, "grant")
    expires_at = payload.get("expires_at", 0)
    if not (client_id and client_secret and access_token and grant):
        return None
    if grant not in OAuthGrant or not isinstance(expires_at, (int, float)):
        return None
    return OAuthCredential(
        client_id=client_id,
        client_secret=client_secret,
        access_token=access_token,
        grant=OAuthGrant(grant),
        refresh_token=_text(payload, "refresh_token"),
        expires_at=float(expires_at),
    )


def decode(raw: str) -> Credential | None:
    try:
        payload: object = json.loads(raw)
    except ValueError:
        return None
    if not isinstance(payload, dict):
        return None
    kind = payload.get("kind")
    if kind == "api_token":
        email, api_token = _text(payload, "email"), _text(payload, "api_token")
        return ApiTokenCredential(email=email, api_token=api_token) if email and api_token else None
    if kind == "access_token":
        access_token = _text(payload, "access_token")
        return AccessTokenCredential(access_token=access_token) if access_token else None
    if kind == "oauth":
        return _decode_oauth(payload)
    return None


class CredentialStore(Protocol):
    @property
    def source(self) -> CredentialSource: ...

    def get(self, profile: str) -> Credential | None: ...


class WritableCredentialStore(CredentialStore, Protocol):
    def available(self) -> bool: ...

    def set(self, profile: str, credential: Credential) -> None: ...

    def delete(self, profile: str) -> bool: ...

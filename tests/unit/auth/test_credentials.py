from __future__ import annotations

import json
import string
from typing import Final

import pytest

from bitbucket_unofficial_cli.auth.credentials import AccessTokenCredential
from bitbucket_unofficial_cli.auth.credentials import ApiTokenCredential
from bitbucket_unofficial_cli.auth.credentials import Credential
from bitbucket_unofficial_cli.auth.credentials import OAuthCredential
from bitbucket_unofficial_cli.auth.credentials import OAuthGrant
from bitbucket_unofficial_cli.auth.credentials import decode
from bitbucket_unofficial_cli.auth.credentials import encode
from bitbucket_unofficial_cli.auth.credentials import mask

OAUTH: Final = OAuthCredential(
    client_id="key",
    client_secret="secret",
    access_token="access-1234",
    grant=OAuthGrant.AUTHORIZATION_CODE,
    refresh_token="refresh",
    expires_at=1234.5,
)


@pytest.mark.parametrize(
    "credential",
    [ApiTokenCredential(email="a@b.c", api_token="tok"), AccessTokenCredential(access_token="bearer"), OAUTH],
)
def test_encode_then_decode_round_trips(credential: Credential) -> None:
    # Arrange
    raw = encode(credential)
    # Act
    decoded = decode(raw)
    # Assert
    assert decoded == credential


@pytest.mark.parametrize(
    "raw",
    [
        "not json",
        "[]",
        '{"kind": "mystery"}',
        '{"kind": "api_token", "email": "a@b.c"}',
        '{"kind": "access_token", "access_token": ""}',
        '{"kind": "oauth", "client_id": "k"}',
        json.dumps({**json.loads(encode(OAUTH)), "grant": "password"}),
        json.dumps({**json.loads(encode(OAUTH)), "expires_at": "soon"}),
    ],
)
def test_decode_rejects_malformed_payloads(raw: str) -> None:
    # Arrange
    # Act
    decoded = decode(raw)
    # Assert
    assert decoded is None


def test_oauth_without_refresh_token_round_trips() -> None:
    # Arrange
    credential = OAuthCredential(
        client_id="k", client_secret="s", access_token="a", grant=OAuthGrant.CLIENT_CREDENTIALS
    )
    # Act
    decoded = decode(encode(credential))
    # Assert
    assert decoded == credential


def test_mask_keeps_only_the_last_characters() -> None:
    # Arrange
    # Act
    # Assert
    assert mask(string.digits) == "********6789"
    assert mask("abc") == "***"
    assert ApiTokenCredential(email="e", api_token="12345678").masked() == "********5678"
    assert AccessTokenCredential(access_token="12345678").masked() == "********5678"
    assert OAUTH.masked() == "********1234"

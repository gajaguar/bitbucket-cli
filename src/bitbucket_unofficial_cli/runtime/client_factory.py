from __future__ import annotations

import sys
from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING

from bitbucket import BitbucketClient
from bitbucket import ClientOptions

from bitbucket_unofficial_cli.auth.credentials import AccessTokenCredential
from bitbucket_unofficial_cli.auth.credentials import ApiTokenCredential
from bitbucket_unofficial_cli.auth.oauth import OAuthTokenProvider

if TYPE_CHECKING:
    from bitbucket_unofficial_cli.auth.credentials import Credential
    from bitbucket_unofficial_cli.auth.credentials import OAuthCredential
    from bitbucket_unofficial_cli.auth.oauth import OAuthClient


def _ignore(credential: OAuthCredential) -> None:
    del credential


# Per-invocation bundle so the client factory can build a verbose request hook and a token provider
# without growing a long positional argument list every time a new flag appears.
@dataclass(frozen=True, slots=True)
class ClientRequest:
    credential: Credential
    oauth: OAuthClient
    on_renew: Callable[[OAuthCredential], None] = _ignore
    verbose: bool = False


type ClientFactory = Callable[[ClientRequest], BitbucketClient]  # pylint: disable=gajaguar-module-const-naming


def _log_response(response: object) -> None:
    raw_request = getattr(response, "request", None)
    method = getattr(raw_request, "method", "?")
    url = str(getattr(raw_request, "url", "?"))
    status = getattr(response, "status_code", "?")
    sys.stderr.write(f"-> {method} {url} {status}\n")
    sys.stderr.flush()


def event_hooks(*, verbose: bool) -> dict[str, list[Callable[..., object]]] | None:
    return {"response": [_log_response]} if verbose else None


# The credential kind decides the header the SDK sends: Basic for an API token, Bearer for the
# rest. An OAuth credential goes in as a provider, so the SDK asks for the token on every request.
def build_client(request: ClientRequest, options: ClientOptions) -> BitbucketClient:
    credential = request.credential
    if isinstance(credential, ApiTokenCredential):
        return BitbucketClient(email=credential.email, api_token=credential.api_token, options=options)
    if isinstance(credential, AccessTokenCredential):
        return BitbucketClient(access_token=credential.access_token, options=options)
    provider = OAuthTokenProvider(credential, request.oauth, request.on_renew)
    return BitbucketClient(access_token=provider, options=options)


def create_sdk_client(request: ClientRequest) -> BitbucketClient:
    return build_client(request, ClientOptions(event_hooks=event_hooks(verbose=request.verbose)))

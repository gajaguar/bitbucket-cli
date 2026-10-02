from __future__ import annotations

from typing import TYPE_CHECKING

from bitbucket.config import ACCESS_TOKEN_ENV_VAR
from bitbucket.config import API_TOKEN_ENV_VAR
from bitbucket.config import EMAIL_ENV_VAR

from bitbucket_unofficial_cli.auth.credentials import AccessTokenCredential
from bitbucket_unofficial_cli.auth.credentials import ApiTokenCredential
from bitbucket_unofficial_cli.auth.credentials import CredentialSource
from bitbucket_unofficial_cli.runtime.errors import CliError
from bitbucket_unofficial_cli.runtime.exit_codes import ExitCode

if TYPE_CHECKING:
    from collections.abc import Mapping


# The environment credential is profile-agnostic: it overrides whatever profile is selected, for CI.
# It reads the variables the SDK documents, and refuses to guess when both kinds are set, as the SDK does.
class EnvCredentialStore:
    def __init__(self, environ: Mapping[str, str]) -> None:
        self._environ = environ

    @property
    def source(self) -> CredentialSource:
        return CredentialSource.ENVIRONMENT

    def get(self, profile: str) -> ApiTokenCredential | AccessTokenCredential | None:
        del profile
        email = self._environ.get(EMAIL_ENV_VAR)
        api_token = self._environ.get(API_TOKEN_ENV_VAR)
        access_token = self._environ.get(ACCESS_TOKEN_ENV_VAR)
        has_api_token = bool(email and api_token)
        if has_api_token and access_token:
            message = f"Both {API_TOKEN_ENV_VAR} and {ACCESS_TOKEN_ENV_VAR} are set."
            raise CliError(
                message,
                exit_code=ExitCode.CONFIGURATION,
                hint=f"Unset one of them; {ACCESS_TOKEN_ENV_VAR} sends a bearer token, the other sends Basic.",
            )
        if has_api_token and email and api_token:
            return ApiTokenCredential(email=email, api_token=api_token)
        return AccessTokenCredential(access_token=access_token) if access_token else None

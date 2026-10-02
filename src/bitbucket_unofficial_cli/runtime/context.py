from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field
from typing import TYPE_CHECKING

from rich.console import Console

from bitbucket_unofficial_cli.auth.credentials import OAuthCredential
from bitbucket_unofficial_cli.runtime.client_factory import ClientRequest
from bitbucket_unofficial_cli.runtime.errors import CliError
from bitbucket_unofficial_cli.runtime.exit_codes import ExitCode

if TYPE_CHECKING:
    from collections.abc import Callable

    import typer
    from bitbucket import BitbucketClient
    from bitbucket import WorkspaceClient

    from bitbucket_unofficial_cli.auth.credentials import Credential
    from bitbucket_unofficial_cli.auth.credentials import ResolvedCredential
    from bitbucket_unofficial_cli.auth.oauth import OAuthClient
    from bitbucket_unofficial_cli.auth.resolver import CredentialStores
    from bitbucket_unofficial_cli.config.settings import ResolvedOptions
    from bitbucket_unofficial_cli.config.store import SettingsStore
    from bitbucket_unofficial_cli.output.renderer import Dataset
    from bitbucket_unofficial_cli.output.renderer import Renderer
    from bitbucket_unofficial_cli.runtime.client_factory import ClientFactory


@dataclass(frozen=True, slots=True)
class Services:
    settings: SettingsStore
    credentials: CredentialStores
    clients: ClientFactory
    oauth: OAuthClient
    open_browser: Callable[[str], object]


# Built once per invocation by the root callback and shared with every command through
# typer.Context.obj; the SDK client is created lazily so offline commands never need a credential.
@dataclass(slots=True)
class AppContext:
    options: ResolvedOptions
    services: Services
    console: Console
    renderer: Renderer
    _client: BitbucketClient | None = field(default=None, init=False, repr=False)

    def credential(self) -> ResolvedCredential:
        resolved = self.services.credentials.resolve(self.options.profile_name)
        if resolved is None:
            message = f"Not logged in (profile '{self.options.profile_name}')."
            hint = "Run `bitbucket auth login`, or set ATLASSIAN_USER_EMAIL and ATLASSIAN_API_TOKEN."
            raise CliError(message, exit_code=ExitCode.CONFIGURATION, hint=hint)
        return resolved

    # The credential as it is now: an OAuth token that has lapsed is renewed and stored first.
    def fresh_credential(self) -> Credential:
        resolved = self.credential()
        credential = resolved.credential
        if isinstance(credential, OAuthCredential) and self.services.oauth.is_expired(credential):
            credential = self.services.oauth.renew(credential)
            self._store_renewed(resolved, credential)
        return credential

    def client(self) -> BitbucketClient:
        if self._client is None:
            resolved = self.credential()
            request = ClientRequest(
                credential=resolved.credential,
                oauth=self.services.oauth,
                on_renew=lambda renewed: self._store_renewed(resolved, renewed),
                verbose=self.options.verbose,
            )
            self._client = self.services.clients(request)
        return self._client

    def workspace_slug(self) -> str:
        if self.options.workspace is None:
            message = "No workspace selected."
            hint = "Pass --workspace, set BITBUCKET_WORKSPACE, or run `bitbucket workspace use SLUG`."
            raise CliError(message, exit_code=ExitCode.CONFIGURATION, hint=hint)
        return self.options.workspace

    def workspace(self) -> WorkspaceClient:
        return self.client().workspace(self.workspace_slug())

    # A renewed OAuth token goes back to the store it came from, so the next command starts with it.
    def _store_renewed(self, resolved: ResolvedCredential, renewed: OAuthCredential) -> None:
        for store in self.services.credentials.writable():
            if store.source is resolved.source:
                store.set(self.options.profile_name, renewed)

    # Status messages go to stderr so stdout stays clean for piping rendered data.
    @staticmethod
    def notify(message: str) -> None:
        Console(stderr=True, highlight=False).print(message, markup=False)

    def render(self, dataset: Dataset) -> None:
        self.renderer.render(dataset)

    def close(self) -> None:
        if self._client is not None:
            self._client.close()
            self._client = None


def get_app_context(ctx: typer.Context) -> AppContext:
    obj: object = ctx.find_root().obj
    if not isinstance(obj, AppContext):
        message = "CLI context is not initialized."
        raise CliError(message)
    return obj

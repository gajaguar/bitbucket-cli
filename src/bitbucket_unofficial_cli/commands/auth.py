import sys
from dataclasses import dataclass
from datetime import UTC
from datetime import datetime
from os import environ
from typing import TYPE_CHECKING
from typing import Annotated
from typing import Final

import typer

from bitbucket_unofficial_cli.auth.authorization_code import AuthorizationCodeFlow
from bitbucket_unofficial_cli.auth.callback_server import DEFAULT_PORT
from bitbucket_unofficial_cli.auth.credentials import AccessTokenCredential
from bitbucket_unofficial_cli.auth.credentials import ApiTokenCredential
from bitbucket_unofficial_cli.auth.credentials import Credential
from bitbucket_unofficial_cli.auth.credentials import OAuthCredential
from bitbucket_unofficial_cli.auth.credentials import ResolvedCredential
from bitbucket_unofficial_cli.auth.oauth import OAuthConsumer
from bitbucket_unofficial_cli.config.settings import Profile
from bitbucket_unofficial_cli.output.columns import AUTH_STATUS
from bitbucket_unofficial_cli.output.renderer import single
from bitbucket_unofficial_cli.runtime.client_factory import ClientRequest
from bitbucket_unofficial_cli.runtime.context import AppContext
from bitbucket_unofficial_cli.runtime.context import get_app_context
from bitbucket_unofficial_cli.runtime.errors import CliError
from bitbucket_unofficial_cli.runtime.errors import handle_errors
from bitbucket_unofficial_cli.runtime.exit_codes import ExitCode
from bitbucket_unofficial_cli.runtime.params import options_from

if TYPE_CHECKING:
    from bitbucket import BitbucketClient

    from bitbucket_unofficial_cli.auth.credentials import WritableCredentialStore
    from bitbucket_unofficial_cli.auth.resolver import CredentialStores

APP: Final = typer.Typer(help="Log in, inspect, and remove Bitbucket credentials.", no_args_is_help=True)

CLIENT_ID_ENV_VAR: Final = "BITBUCKET_OAUTH_CLIENT_ID"
CLIENT_SECRET_ENV_VAR: Final = "BITBUCKET_OAUTH_CLIENT_SECRET"  # ruff: ignore[hardcoded-password-string]
EMAIL_ENV_VAR: Final = "ATLASSIAN_USER_EMAIL"


@dataclass(frozen=True, slots=True)
class _LoginOptions:
    api_token: Annotated[
        bool,
        typer.Option("--api-token", help="Store an Atlassian API token with your email (the default)."),
    ] = False
    access_token: Annotated[
        bool,
        typer.Option("--access-token", help="Store a repository, project or workspace access token, or any bearer."),
    ] = False
    oauth: Annotated[bool, typer.Option("--oauth", help="Authorize an OAuth consumer and store its tokens.")] = False
    email: Annotated[
        str | None,
        typer.Option("--email", envvar=EMAIL_ENV_VAR, help="Atlassian account email, for --api-token."),
    ] = None
    client_id: Annotated[
        str | None,
        typer.Option("--client-id", envvar=CLIENT_ID_ENV_VAR, help="OAuth consumer key, for --oauth."),
    ] = None
    client_credentials: Annotated[
        bool,
        typer.Option("--client-credentials", help="With --oauth, use the client credentials grant: no browser."),
    ] = False
    callback_port: Annotated[
        int,
        typer.Option("--callback-port", help="With --oauth, the local port of the consumer's callback URL."),
    ] = DEFAULT_PORT
    no_browser: Annotated[
        bool,
        typer.Option("--no-browser", help="With --oauth, paste the redirect address instead of opening a browser."),
    ] = False
    with_token: Annotated[
        bool,
        typer.Option("--with-token", help="Read the secret (token or consumer secret) from standard input."),
    ] = False
    insecure_storage: Annotated[
        bool,
        typer.Option(
            "--insecure-storage", help="Store the credential in a 0600 plaintext file instead of the keyring."
        ),
    ] = False


# No secret flag on purpose: a value passed as an argument ends up in shell history. Standard input
# gives one line, so a later prompt (the pasted redirect address) can still read the next.
def _secret(label: str, *, from_stdin: bool, configured: str | None = None) -> str:
    raw = configured or (sys.stdin.readline() if from_stdin else typer.prompt(label, hide_input=True, err=True))
    secret = str(raw).strip()
    if not secret:
        message = f"The {label.lower()} is empty."
        raise CliError(message, exit_code=ExitCode.USAGE)
    return secret


def _text(label: str, value: str | None) -> str:
    text = str(value or typer.prompt(label, err=True)).strip()
    if not text:
        message = f"The {label.lower()} is empty."
        raise CliError(message, exit_code=ExitCode.USAGE)
    return text


def _validate_mode(options: _LoginOptions) -> None:
    if sum((options.api_token, options.access_token, options.oauth)) > 1:
        message = "Choose one of --api-token, --access-token and --oauth."
        raise CliError(message, exit_code=ExitCode.USAGE)


def _authorize_oauth(app_context: AppContext, options: _LoginOptions) -> OAuthCredential:
    consumer = OAuthConsumer(
        client_id=_text("OAuth consumer key", options.client_id),
        client_secret=_secret(
            "OAuth consumer secret",
            from_stdin=options.with_token,
            configured=environ.get(CLIENT_SECRET_ENV_VAR),
        ),
    )
    oauth = app_context.services.oauth
    if options.client_credentials:
        return oauth.client_credentials(consumer)
    flow = AuthorizationCodeFlow(
        oauth=oauth,
        open_browser=app_context.services.open_browser,
        notify=app_context.notify,
        read_redirect=lambda: str(typer.prompt("Redirect address", err=True)),
    )
    return flow.authorize(consumer, port=options.callback_port, use_browser=not options.no_browser)


def _read_credential(app_context: AppContext, options: _LoginOptions) -> Credential:
    _validate_mode(options)
    if options.oauth:
        return _authorize_oauth(app_context, options)
    if options.access_token:
        return AccessTokenCredential(access_token=_secret("Access token", from_stdin=options.with_token))
    email = _text("Atlassian email", options.email)
    return ApiTokenCredential(email=email, api_token=_secret("Atlassian API token", from_stdin=options.with_token))


def _select_store(stores: CredentialStores, *, insecure_storage: bool) -> WritableCredentialStore:
    if insecure_storage:
        return stores.file
    if stores.keyring.available():
        return stores.keyring
    message = "No system keyring backend is available."
    raise CliError(
        message,
        exit_code=ExitCode.CONFIGURATION,
        hint="Retry with --insecure-storage, or set ATLASSIAN_API_TOKEN or BITBUCKET_ACCESS_TOKEN in the environment.",
    )


# Access tokens are scoped to one repository, project or workspace and cannot read /user, so they are
# checked against the selected workspace instead, and skipped when none is selected yet.
def _identify(
    app_context: AppContext,
    client: BitbucketClient,
    credential: Credential,
) -> tuple[str | None, str | None]:
    if isinstance(credential, AccessTokenCredential):
        if app_context.options.workspace is None:
            app_context.notify("Access token not validated: no workspace selected (use --workspace).")
        else:
            client.workspace(app_context.options.workspace).get()
        return None, None
    user = client.user.me()
    return user.display_name, user.account_id


def _expiry(credential: Credential) -> str | None:
    if isinstance(credential, OAuthCredential) and credential.expires_at > 0:
        return datetime.fromtimestamp(credential.expires_at, UTC).isoformat(timespec="seconds")
    return None


def _status_record(app_context: AppContext, resolved: ResolvedCredential, user: str | None) -> dict[str, object]:
    credential = resolved.credential
    return {
        "profile": app_context.options.profile_name,
        "user": user or "(access token)",
        "kind": credential.kind,
        "source": resolved.source,
        "expiresAt": _expiry(credential),
        "secret": credential.masked(),
    }


def _save_profile(app_context: AppContext, user: str | None, account_id: str | None) -> None:
    name = app_context.options.profile_name
    store = app_context.services.settings
    settings = store.load()
    existing = settings.profiles.get(name, Profile())
    profile = Profile(
        workspace=app_context.options.workspace or existing.workspace,
        account_id=account_id,
        display_name=user,
    )
    if not settings.profiles:
        settings = settings.model_copy(update={"default_profile": name})
    store.save(settings.with_profile(name, profile))


@APP.command(help="Validate a credential and store it for the selected profile.")
@handle_errors
@options_from(_LoginOptions)
def login(ctx: typer.Context, options: _LoginOptions) -> None:
    app_context = get_app_context(ctx)
    stores = app_context.services.credentials
    profile_name = app_context.options.profile_name
    credential = _read_credential(app_context, options)
    store = _select_store(stores, insecure_storage=options.insecure_storage)

    # Validate through a throwaway client: nothing is stored until the credential is known to work.
    request = ClientRequest(
        credential=credential, oauth=app_context.services.oauth, verbose=app_context.options.verbose
    )
    with app_context.services.clients(request) as client:
        user, account_id = _identify(app_context, client, credential)

    store.set(profile_name, credential)
    for other in stores.writable():
        if other is not store:
            other.delete(profile_name)
    _save_profile(app_context, user, account_id)

    app_context.notify(f"Logged in to profile '{profile_name}' ({store.source}).")
    resolved = ResolvedCredential(credential=credential, source=store.source)
    app_context.render(single(_status_record(app_context, resolved, user), AUTH_STATUS, id_key="profile"))


@APP.command(help="Show the active credential and the user it belongs to.")
@handle_errors
def status(ctx: typer.Context) -> None:
    app_context = get_app_context(ctx)
    resolved = app_context.credential()
    user, _ = _identify(app_context, app_context.client(), resolved.credential)
    app_context.render(single(_status_record(app_context, resolved, user), AUTH_STATUS, id_key="profile"))


@APP.command(help="Renew the stored OAuth token now.")
@handle_errors
def refresh(ctx: typer.Context) -> None:
    app_context = get_app_context(ctx)
    resolved = app_context.credential()
    if not isinstance(resolved.credential, OAuthCredential):
        message = f"Only OAuth credentials can be refreshed; this one is '{resolved.credential.kind}'."
        raise CliError(message, exit_code=ExitCode.USAGE)
    renewed = app_context.services.oauth.renew(resolved.credential)
    for store in app_context.services.credentials.writable():
        if store.source is resolved.source:
            store.set(app_context.options.profile_name, renewed)
    app_context.notify(f"Token renewed; it expires {_expiry(renewed) or 'at an unknown time'}.")


@APP.command(help="Remove the stored credential and profile.")
@handle_errors
def logout(ctx: typer.Context) -> None:
    app_context = get_app_context(ctx)
    services = app_context.services
    profile_name = app_context.options.profile_name

    removed = [store.source for store in services.credentials.writable() if store.delete(profile_name)]
    settings = services.settings.load()
    had_profile = profile_name in settings.profiles
    if had_profile:
        services.settings.save(settings.without_profile(profile_name))
    if not removed and not had_profile:
        message = f"No stored credentials for profile '{profile_name}'."
        raise CliError(message, exit_code=ExitCode.CONFIGURATION)

    app_context.notify(f"Logged out of profile '{profile_name}'.")
    if services.credentials.environment.get(profile_name) is not None:
        app_context.notify("A credential is still set in the environment and will keep being used.")


@APP.command(help="Print the API token, or the bearer token, of the active credential.")
@handle_errors
def token(ctx: typer.Context) -> None:
    credential = get_app_context(ctx).fresh_credential()
    typer.echo(credential.api_token if isinstance(credential, ApiTokenCredential) else credential.access_token)

from dataclasses import dataclass
from pathlib import Path
from typing import Annotated
from typing import Final

import typer
from bitbucket.models.gpg_key import GpgKeyCreate
from bitbucket.models.ssh_key import SshKeyCreate
from bitbucket.models.ssh_key import SshKeyUpdate

from bitbucket_unofficial_cli.output.columns import EMAILS
from bitbucket_unofficial_cli.output.columns import GPG_KEYS
from bitbucket_unofficial_cli.output.columns import SSH_KEYS
from bitbucket_unofficial_cli.output.renderer import many
from bitbucket_unofficial_cli.output.renderer import single
from bitbucket_unofficial_cli.runtime.context import get_app_context
from bitbucket_unofficial_cli.runtime.errors import CliError
from bitbucket_unofficial_cli.runtime.errors import handle_errors
from bitbucket_unofficial_cli.runtime.exit_codes import ExitCode
from bitbucket_unofficial_cli.runtime.params import FromFile
from bitbucket_unofficial_cli.runtime.params import PagingOptions
from bitbucket_unofficial_cli.runtime.params import options_from
from bitbucket_unofficial_cli.services.accounts import selected_user
from bitbucket_unofficial_cli.services.listing import paged
from bitbucket_unofficial_cli.services.payloads import build

EMAIL_APP: Final = typer.Typer(help="Email addresses of the authenticated user.", no_args_is_help=True)
SSH_APP: Final = typer.Typer(help="SSH keys of a user.", no_args_is_help=True)
GPG_APP: Final = typer.Typer(help="GPG keys of a user.", no_args_is_help=True)

KeyId = Annotated[str, typer.Argument(help="SSH key UUID.")]  # pylint: disable=gajaguar-module-const-naming,gajaguar-require-final
Fingerprint = Annotated[str, typer.Argument(help="GPG key fingerprint.")]  # pylint: disable=gajaguar-module-const-naming,gajaguar-require-final
_User = Annotated[str | None, typer.Option("--user", help="Account ID or UUID; defaults to you.")]  # pylint: disable=gajaguar-module-const-naming,gajaguar-require-final


@dataclass(frozen=True, slots=True, kw_only=True)
class _ListOptions(PagingOptions):
    user: _User = None


@dataclass(frozen=True, slots=True, kw_only=True)
class _SshCreateOptions:
    user: _User = None
    key: Annotated[str | None, typer.Option("--key", help="SSH public key.")] = None
    key_file: Annotated[Path | None, typer.Option("--key-file", help="File with the SSH public key.")] = None
    label: Annotated[str | None, typer.Option("--label", help="Label for the key.")] = None
    expires_on: Annotated[str | None, typer.Option("--expires-on", help="Expiry as an ISO 8601 date and time.")] = None
    from_file: FromFile = None


@dataclass(frozen=True, slots=True, kw_only=True)
class _SshUpdateOptions:
    key_id: KeyId
    user: _User = None
    label: Annotated[str | None, typer.Option("--label", help="New label.")] = None


@dataclass(frozen=True, slots=True, kw_only=True)
class _SshKeyOptions:
    key_id: KeyId
    user: _User = None
    yes: Annotated[bool, typer.Option("--yes", "-y", help="Do not ask for confirmation.")] = False


@dataclass(frozen=True, slots=True, kw_only=True)
class _GpgCreateOptions:
    user: _User = None
    key: Annotated[str | None, typer.Option("--key", help="ASCII-armored GPG public key.")] = None
    key_file: Annotated[Path | None, typer.Option("--key-file", help="File with the GPG public key.")] = None
    name: Annotated[str | None, typer.Option("--name", help="Name for the key.")] = None
    from_file: FromFile = None


@dataclass(frozen=True, slots=True, kw_only=True)
class _GpgKeyOptions:
    fingerprint: Fingerprint
    user: _User = None
    yes: Annotated[bool, typer.Option("--yes", "-y", help="Do not ask for confirmation.")] = False


def _public_key(key: str | None, key_file: Path | None) -> str | None:
    if key_file is None:
        return key
    try:
        return key_file.read_text(encoding="utf-8").strip()
    except OSError as error:
        message = f"Cannot read {key_file}: {error}"
        raise CliError(message, exit_code=ExitCode.USAGE) from error


@EMAIL_APP.command(name="list", help="List your email addresses.")
@handle_errors
@options_from(PagingOptions)
def list_emails(ctx: typer.Context, options: PagingOptions) -> None:
    app_context = get_app_context(ctx)
    user = app_context.client().user
    found = paged(app_context, options, user.emails, user.emails_page)
    app_context.render(many(found, EMAILS, id_key="email"))


@EMAIL_APP.command(name="get", help="Show one of your email addresses.")
@handle_errors
def get_email(ctx: typer.Context, address: Annotated[str, typer.Argument(help="Email address.")]) -> None:
    app_context = get_app_context(ctx)
    app_context.render(single(app_context.client().user.email(address), EMAILS, id_key="email"))


@SSH_APP.command(name="list", help="List SSH keys.")
@handle_errors
@options_from(_ListOptions)
def list_ssh_keys(ctx: typer.Context, options: _ListOptions) -> None:
    app_context = get_app_context(ctx)
    keys = app_context.client().users(selected_user(app_context, options.user)).ssh_keys
    found = paged(app_context, options, keys.list, keys.list_page)
    app_context.render(many(found, SSH_KEYS, id_key="uuid"))


@SSH_APP.command(name="get", help="Show an SSH key.")
@handle_errors
def get_ssh_key(ctx: typer.Context, key_id: KeyId, user: _User = None) -> None:
    app_context = get_app_context(ctx)
    keys = app_context.client().users(selected_user(app_context, user)).ssh_keys
    app_context.render(single(keys.get(key_id), SSH_KEYS, id_key="uuid"))


@SSH_APP.command(name="create", help="Add an SSH key.")
@handle_errors
@options_from(_SshCreateOptions)
def create_ssh_key(ctx: typer.Context, options: _SshCreateOptions) -> None:
    app_context = get_app_context(ctx)
    payload = build(
        SshKeyCreate, options.from_file, key=_public_key(options.key, options.key_file), label=options.label
    )
    keys = app_context.client().users(selected_user(app_context, options.user)).ssh_keys
    app_context.render(single(keys.create(payload, expires_on=options.expires_on), SSH_KEYS, id_key="uuid"))


@SSH_APP.command(name="update", help="Change the label of an SSH key.")
@handle_errors
@options_from(_SshUpdateOptions)
def update_ssh_key(ctx: typer.Context, options: _SshUpdateOptions) -> None:
    app_context = get_app_context(ctx)
    keys = app_context.client().users(selected_user(app_context, options.user)).ssh_keys
    updated = keys.update(options.key_id, build(SshKeyUpdate, label=options.label))
    app_context.render(single(updated, SSH_KEYS, id_key="uuid"))


@SSH_APP.command(name="delete", help="Delete an SSH key.")
@handle_errors
@options_from(_SshKeyOptions)
def delete_ssh_key(ctx: typer.Context, options: _SshKeyOptions) -> None:
    app_context = get_app_context(ctx)
    keys = app_context.client().users(selected_user(app_context, options.user)).ssh_keys
    app_context.confirm(f"Delete SSH key '{options.key_id}'?", assume_yes=options.yes)
    keys.delete(options.key_id)
    app_context.notify(f"Deleted SSH key '{options.key_id}'.")


@GPG_APP.command(name="list", help="List GPG keys.")
@handle_errors
@options_from(_ListOptions)
def list_gpg_keys(ctx: typer.Context, options: _ListOptions) -> None:
    app_context = get_app_context(ctx)
    keys = app_context.client().users(selected_user(app_context, options.user)).gpg_keys
    found = paged(app_context, options, keys.list, keys.list_page)
    app_context.render(many(found, GPG_KEYS, id_key="fingerprint"))


@GPG_APP.command(name="get", help="Show a GPG key.")
@handle_errors
def get_gpg_key(ctx: typer.Context, fingerprint: Fingerprint, user: _User = None) -> None:
    app_context = get_app_context(ctx)
    keys = app_context.client().users(selected_user(app_context, user)).gpg_keys
    app_context.render(single(keys.get(fingerprint), GPG_KEYS, id_key="fingerprint"))


@GPG_APP.command(name="create", help="Add a GPG key.")
@handle_errors
@options_from(_GpgCreateOptions)
def create_gpg_key(ctx: typer.Context, options: _GpgCreateOptions) -> None:
    app_context = get_app_context(ctx)
    payload = build(GpgKeyCreate, options.from_file, key=_public_key(options.key, options.key_file), name=options.name)
    keys = app_context.client().users(selected_user(app_context, options.user)).gpg_keys
    app_context.render(single(keys.create(payload), GPG_KEYS, id_key="fingerprint"))


@GPG_APP.command(name="delete", help="Delete a GPG key.")
@handle_errors
@options_from(_GpgKeyOptions)
def delete_gpg_key(ctx: typer.Context, options: _GpgKeyOptions) -> None:
    app_context = get_app_context(ctx)
    keys = app_context.client().users(selected_user(app_context, options.user)).gpg_keys
    app_context.confirm(f"Delete GPG key '{options.fingerprint}'?", assume_yes=options.yes)
    keys.delete(options.fingerprint)
    app_context.notify(f"Deleted GPG key '{options.fingerprint}'.")

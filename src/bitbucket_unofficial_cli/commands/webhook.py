from dataclasses import dataclass
from typing import TYPE_CHECKING
from typing import Annotated
from typing import Final

import typer
from bitbucket.models.hook import WebhookCreate
from bitbucket.models.hook import WebhookUpdate

from bitbucket_unofficial_cli.output.columns import WEBHOOK
from bitbucket_unofficial_cli.output.columns import WEBHOOKS
from bitbucket_unofficial_cli.output.renderer import many
from bitbucket_unofficial_cli.output.renderer import single
from bitbucket_unofficial_cli.runtime.context import AppContext
from bitbucket_unofficial_cli.runtime.context import get_app_context
from bitbucket_unofficial_cli.runtime.errors import handle_errors
from bitbucket_unofficial_cli.runtime.params import FromFile
from bitbucket_unofficial_cli.runtime.params import OptionalRepo
from bitbucket_unofficial_cli.runtime.params import PagingOptions
from bitbucket_unofficial_cli.runtime.params import Yes
from bitbucket_unofficial_cli.runtime.params import options_from
from bitbucket_unofficial_cli.services.listing import paged
from bitbucket_unofficial_cli.services.payloads import build

if TYPE_CHECKING:
    from bitbucket.resources.hooks import HooksResource

APP: Final = typer.Typer(
    help="Manage webhooks of a repository (--repo), or of the workspace without it.", no_args_is_help=True
)

Uuid = Annotated[str, typer.Argument(help="Webhook UUID.")]  # pylint: disable=gajaguar-module-const-naming,gajaguar-require-final


def _hooks(app_context: AppContext, repo: str | None) -> HooksResource:
    workspace = app_context.workspace()
    return app_context.repository(repo).hooks if repo else workspace.hooks


@dataclass(frozen=True, slots=True, kw_only=True)
class _ListOptions(PagingOptions):
    repo: OptionalRepo = None


@dataclass(frozen=True, slots=True, kw_only=True)
class _WriteOptions:
    repo: OptionalRepo = None
    description: Annotated[str | None, typer.Option("--description", help="What the webhook is for.")] = None
    url: Annotated[str | None, typer.Option("--url", help="URL that receives the events.")] = None
    events: Annotated[
        list[str] | None,
        typer.Option("--event", help="Event to subscribe to, e.g. repo:push; repeatable."),
    ] = None
    active: Annotated[bool | None, typer.Option("--active/--inactive", help="Whether it fires.")] = None
    from_file: FromFile = None


@dataclass(frozen=True, slots=True, kw_only=True)
class _UpdateOptions(_WriteOptions):
    uuid: Uuid


@APP.command(name="list", help="List webhooks.")
@handle_errors
@options_from(_ListOptions)
def list_webhooks(ctx: typer.Context, options: _ListOptions) -> None:
    app_context = get_app_context(ctx)
    hooks = _hooks(app_context, options.repo)
    found = paged(app_context, options, hooks.list, hooks.list_page)
    app_context.render(many(found, WEBHOOKS))


@APP.command(help="Show a webhook.")
@handle_errors
def get(ctx: typer.Context, uuid: Uuid, repo: OptionalRepo = None) -> None:
    app_context = get_app_context(ctx)
    app_context.render(single(_hooks(app_context, repo).get(uuid), WEBHOOK))


@APP.command(help="Create a webhook.")
@handle_errors
@options_from(_WriteOptions)
def create(ctx: typer.Context, options: _WriteOptions) -> None:
    app_context = get_app_context(ctx)
    payload = build(
        WebhookCreate,
        options.from_file,
        description=options.description,
        url=options.url,
        events=options.events,
        active=options.active,
    )
    app_context.render(single(_hooks(app_context, options.repo).create(payload), WEBHOOK))


@APP.command(help="Update a webhook.")
@handle_errors
@options_from(_UpdateOptions)
def update(ctx: typer.Context, options: _UpdateOptions) -> None:
    app_context = get_app_context(ctx)
    payload = build(
        WebhookUpdate,
        options.from_file,
        description=options.description,
        url=options.url,
        events=options.events,
        active=options.active,
    )
    app_context.render(single(_hooks(app_context, options.repo).update(options.uuid, payload), WEBHOOK))


@APP.command(help="Delete a webhook.")
@handle_errors
def delete(ctx: typer.Context, uuid: Uuid, repo: OptionalRepo = None, *, yes: Yes = False) -> None:
    app_context = get_app_context(ctx)
    app_context.confirm(f"Delete webhook '{uuid}'?", assume_yes=yes)
    _hooks(app_context, repo).delete(uuid)
    app_context.notify(f"Deleted webhook '{uuid}'.")

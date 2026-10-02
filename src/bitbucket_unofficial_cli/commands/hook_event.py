from dataclasses import dataclass
from typing import Annotated
from typing import Final

import typer

from bitbucket_unofficial_cli.output.columns import HOOK_EVENTS
from bitbucket_unofficial_cli.output.renderer import Column
from bitbucket_unofficial_cli.output.renderer import many
from bitbucket_unofficial_cli.runtime.context import get_app_context
from bitbucket_unofficial_cli.runtime.errors import handle_errors
from bitbucket_unofficial_cli.runtime.params import PagingOptions
from bitbucket_unofficial_cli.runtime.params import options_from
from bitbucket_unofficial_cli.services.listing import paged

APP: Final = typer.Typer(help="List the events a webhook can subscribe to.", no_args_is_help=True)

_SUBJECT_TYPES: Final = (Column("subject_type", "Subject type"), Column("links.events.href", "Events URL"))


@dataclass(frozen=True, slots=True, kw_only=True)
class _ListOptions(PagingOptions):
    subject_type: Annotated[str, typer.Argument(help="repository, workspace, user or team.")]


@APP.command(name="types", help="List the subject types that have webhook events.")
@handle_errors
def subject_types(ctx: typer.Context) -> None:
    app_context = get_app_context(ctx)
    found = app_context.client().hook_events.subject_types()
    records = [{"subject_type": name, **item.model_dump(mode="json")} for name, item in found.items()]
    app_context.render(many(records, _SUBJECT_TYPES, id_key="subject_type"))


@APP.command(name="list", help="List the events of one subject type.")
@handle_errors
@options_from(_ListOptions)
def list_events(ctx: typer.Context, options: _ListOptions) -> None:
    app_context = get_app_context(ctx)
    events = app_context.client().hook_events
    subject = options.subject_type
    found = paged(
        app_context,
        options,
        lambda: events.list(subject),
        lambda **page: events.list_page(subject, **page),
    )
    app_context.render(many(found, HOOK_EVENTS, id_key="event"))

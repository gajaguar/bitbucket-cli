from dataclasses import dataclass
from typing import Annotated
from typing import Final

import typer

from bitbucket_unofficial_cli.output.columns import WORKSPACE
from bitbucket_unofficial_cli.output.columns import WORKSPACES
from bitbucket_unofficial_cli.output.renderer import many
from bitbucket_unofficial_cli.output.renderer import single
from bitbucket_unofficial_cli.runtime.context import get_app_context
from bitbucket_unofficial_cli.runtime.errors import CliError
from bitbucket_unofficial_cli.runtime.errors import handle_errors
from bitbucket_unofficial_cli.runtime.exit_codes import ExitCode
from bitbucket_unofficial_cli.runtime.params import PagingOptions
from bitbucket_unofficial_cli.runtime.params import options_from
from bitbucket_unofficial_cli.services.listing import ListOptions
from bitbucket_unofficial_cli.services.listing import collect

APP: Final = typer.Typer(help="Inspect and select the Bitbucket workspace.", no_args_is_help=True)


@dataclass(frozen=True, slots=True, kw_only=True)
class _ListOptions(PagingOptions):
    administrator: Annotated[
        bool,
        typer.Option("--administrator", help="Only workspaces where you are an administrator."),
    ] = False


@APP.command(name="list", help="List the workspaces the credential can access.")
@handle_errors
@options_from(_ListOptions)
def list_workspaces(ctx: typer.Context, options: _ListOptions) -> None:
    app_context = get_app_context(ctx)
    user = app_context.client().user
    administrator = True if options.administrator else None
    workspaces = collect(
        lambda: user.workspaces(administrator=administrator),
        lambda **page: user.workspaces_page(administrator=administrator, **page),
        ListOptions(limit=options.limit, cursor=options.cursor),
        on_next=lambda cursor: app_context.notify(f"next cursor: {cursor}"),
    )
    app_context.render(many(workspaces, WORKSPACES, id_key="workspace.slug"))


@APP.command(help="Show a workspace; defaults to the selected one.")
@handle_errors
def get(
    ctx: typer.Context,
    slug: Annotated[str | None, typer.Argument(help="Workspace slug; defaults to the selected workspace.")] = None,
) -> None:
    app_context = get_app_context(ctx)
    workspace = app_context.client().workspace(slug) if slug else app_context.workspace()
    app_context.render(single(workspace.get(), WORKSPACE, id_key="slug"))


@APP.command(help="Persist the workspace choice in the active profile.")
@handle_errors
def use(ctx: typer.Context, slug: Annotated[str, typer.Argument(help="Workspace slug to make the default.")]) -> None:
    app_context = get_app_context(ctx)
    # Reading it first proves the credential can see the workspace before it becomes the default.
    app_context.client().workspace(slug).get()
    store = app_context.services.settings
    settings = store.load()
    name = app_context.options.profile_name
    if name not in settings.profiles:
        message = f"No profile named '{name}'; run `bitbucket auth login`."
        raise CliError(message, exit_code=ExitCode.CONFIGURATION)
    updated = settings.profiles[name].model_copy(update={"workspace": slug})
    store.save(settings.with_profile(name, updated))
    app_context.notify(f"Workspace set to '{slug}' for profile '{name}'.")

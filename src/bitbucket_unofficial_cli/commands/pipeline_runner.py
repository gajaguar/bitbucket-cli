from dataclasses import dataclass
from typing import TYPE_CHECKING
from typing import Annotated
from typing import Final

import typer
from bitbucket.models.runner import RunnerCreate
from bitbucket.models.runner import RunnerUpdate

from bitbucket_unofficial_cli.output.columns import RUNNERS
from bitbucket_unofficial_cli.output.renderer import many
from bitbucket_unofficial_cli.output.renderer import single
from bitbucket_unofficial_cli.runtime.context import AppContext
from bitbucket_unofficial_cli.runtime.context import get_app_context
from bitbucket_unofficial_cli.runtime.errors import handle_errors
from bitbucket_unofficial_cli.runtime.params import FromFile
from bitbucket_unofficial_cli.runtime.params import OptionalRepo
from bitbucket_unofficial_cli.runtime.params import PagingOptions
from bitbucket_unofficial_cli.runtime.params import options_from
from bitbucket_unofficial_cli.services.listing import paged
from bitbucket_unofficial_cli.services.payloads import build

if TYPE_CHECKING:
    from bitbucket.resources.runners import RunnersResource

APP: Final = typer.Typer(
    help="Self-hosted runners of a repository (--repo), or of the workspace without it.", no_args_is_help=True
)

Uuid = Annotated[str, typer.Argument(help="Runner UUID.")]  # pylint: disable=gajaguar-module-const-naming,gajaguar-require-final


def _runners(app_context: AppContext, repo: str | None) -> RunnersResource:
    if repo:
        return app_context.repository(repo).pipelines_config.runners
    return app_context.workspace().pipelines_config.runners


@dataclass(frozen=True, slots=True, kw_only=True)
class _ListOptions(PagingOptions):
    repo: OptionalRepo = None


@dataclass(frozen=True, slots=True, kw_only=True)
class _WriteOptions:
    repo: OptionalRepo = None
    name: Annotated[str | None, typer.Option("--name", help="Runner name.")] = None
    labels: Annotated[list[str] | None, typer.Option("--label", help="Runner label; repeatable.")] = None
    from_file: FromFile = None


@dataclass(frozen=True, slots=True, kw_only=True)
class _UpdateOptions(_WriteOptions):
    uuid: Uuid


@dataclass(frozen=True, slots=True, kw_only=True)
class _DeleteOptions:
    uuid: Uuid
    repo: OptionalRepo = None
    yes: Annotated[bool, typer.Option("--yes", "-y", help="Do not ask for confirmation.")] = False


@APP.command(name="list", help="List runners.")
@handle_errors
@options_from(_ListOptions)
def list_runners(ctx: typer.Context, options: _ListOptions) -> None:
    app_context = get_app_context(ctx)
    runners = _runners(app_context, options.repo)
    found = paged(app_context, options, runners.list, runners.list_page)
    app_context.render(many(found, RUNNERS, id_key="uuid"))


@APP.command(help="Show a runner.")
@handle_errors
def get(ctx: typer.Context, uuid: Uuid, repo: OptionalRepo = None) -> None:
    app_context = get_app_context(ctx)
    app_context.render(single(_runners(app_context, repo).get(uuid), RUNNERS, id_key="uuid"))


@APP.command(help="Register a runner. Its OAuth credentials are not printed.")
@handle_errors
@options_from(_WriteOptions)
def create(ctx: typer.Context, options: _WriteOptions) -> None:
    app_context = get_app_context(ctx)
    payload = build(RunnerCreate, options.from_file, name=options.name, labels=options.labels)
    app_context.render(single(_runners(app_context, options.repo).create(payload), RUNNERS, id_key="uuid"))


@APP.command(help="Rename a runner or change its labels.")
@handle_errors
@options_from(_UpdateOptions)
def update(ctx: typer.Context, options: _UpdateOptions) -> None:
    app_context = get_app_context(ctx)
    payload = build(RunnerUpdate, options.from_file, name=options.name, labels=options.labels)
    updated = _runners(app_context, options.repo).update(options.uuid, payload)
    app_context.render(single(updated, RUNNERS, id_key="uuid"))


@APP.command(help="Delete a runner.")
@handle_errors
@options_from(_DeleteOptions)
def delete(ctx: typer.Context, options: _DeleteOptions) -> None:
    app_context = get_app_context(ctx)
    app_context.confirm(f"Delete runner '{options.uuid}'?", assume_yes=options.yes)
    _runners(app_context, options.repo).delete(options.uuid)
    app_context.notify(f"Deleted runner '{options.uuid}'.")

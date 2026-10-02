from dataclasses import dataclass
from typing import Annotated
from typing import Final

import typer
from bitbucket.models.branch import BranchCreate

from bitbucket_unofficial_cli.output.columns import BRANCHES
from bitbucket_unofficial_cli.output.renderer import many
from bitbucket_unofficial_cli.output.renderer import single
from bitbucket_unofficial_cli.runtime.context import get_app_context
from bitbucket_unofficial_cli.runtime.errors import handle_errors
from bitbucket_unofficial_cli.runtime.params import PagingOptions
from bitbucket_unofficial_cli.runtime.params import Repo
from bitbucket_unofficial_cli.runtime.params import Yes
from bitbucket_unofficial_cli.runtime.params import options_from
from bitbucket_unofficial_cli.services.listing import paged
from bitbucket_unofficial_cli.services.payloads import build

APP: Final = typer.Typer(help="Manage the branches of a repository.", no_args_is_help=True)

Name = Annotated[str, typer.Argument(help="Branch name.")]  # pylint: disable=gajaguar-module-const-naming,gajaguar-require-final


@dataclass(frozen=True, slots=True, kw_only=True)
class _ListOptions(PagingOptions):
    repo: Repo


@APP.command(name="list", help="List the branches of a repository.")
@handle_errors
@options_from(_ListOptions)
def list_branches(ctx: typer.Context, options: _ListOptions) -> None:
    app_context = get_app_context(ctx)
    branches = app_context.repository(options.repo).refs.branches
    found = paged(app_context, options, branches.list, branches.list_page)
    app_context.render(many(found, BRANCHES, id_key="name"))


@APP.command(help="Show a branch.")
@handle_errors
def get(ctx: typer.Context, name: Name, repo: Repo) -> None:
    app_context = get_app_context(ctx)
    app_context.render(single(app_context.repository(repo).refs.branches.get(name), BRANCHES, id_key="name"))


@APP.command(help="Create a branch at a commit.")
@handle_errors
def create(
    ctx: typer.Context,
    name: Name,
    repo: Repo,
    target: Annotated[str, typer.Option("--target", help="Commit hash the branch starts at.")],
) -> None:
    app_context = get_app_context(ctx)
    payload = build(BranchCreate, name=name, target={"hash": target})
    app_context.render(single(app_context.repository(repo).refs.branches.create(payload), BRANCHES, id_key="name"))


@APP.command(help="Delete a branch.")
@handle_errors
def delete(ctx: typer.Context, name: Name, repo: Repo, *, yes: Yes = False) -> None:
    app_context = get_app_context(ctx)
    app_context.confirm(f"Delete branch '{name}'?", assume_yes=yes)
    app_context.repository(repo).refs.branches.delete(name)
    app_context.notify(f"Deleted branch '{name}'.")

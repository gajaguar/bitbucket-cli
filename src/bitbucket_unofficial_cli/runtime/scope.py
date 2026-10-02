from __future__ import annotations

from typing import TYPE_CHECKING

from bitbucket_unofficial_cli.runtime.errors import CliError
from bitbucket_unofficial_cli.runtime.exit_codes import ExitCode

if TYPE_CHECKING:
    import typer
    from bitbucket import ProjectClient
    from bitbucket import RepositoryClient

    from bitbucket_unofficial_cli.runtime.context import AppContext


def _from_command_line(ctx: typer.Context, name: str) -> bool:
    source = ctx.get_parameter_source(name)
    return source is not None and source.name == "COMMANDLINE"


# Settings that exist on a repository and on a project take --repo or --project. --repo can also
# arrive from BITBUCKET_REPOSITORY, so only an explicit --repo conflicts with --project.
def resolve_scope(
    ctx: typer.Context, app_context: AppContext, repo: str | None, project: str | None
) -> RepositoryClient | ProjectClient:
    if project:
        if repo and _from_command_line(ctx, "repo"):
            message = "--repo and --project cannot be combined."
            raise CliError(message, exit_code=ExitCode.USAGE)
        return app_context.workspace().project(project)
    if repo:
        return app_context.repository(repo)
    message = "Pass --repo or --project."
    raise CliError(message, exit_code=ExitCode.USAGE)


__all__ = ["resolve_scope"]

import os
import sys
import webbrowser
from dataclasses import dataclass
from typing import TYPE_CHECKING
from typing import Annotated
from typing import Final

import typer
from rich.console import Console

from bitbucket_unofficial_cli._version import __version__
from bitbucket_unofficial_cli.auth.env_store import EnvCredentialStore
from bitbucket_unofficial_cli.auth.file_store import FileCredentialStore
from bitbucket_unofficial_cli.auth.keyring_store import KeyringCredentialStore
from bitbucket_unofficial_cli.auth.oauth import OAuthClient
from bitbucket_unofficial_cli.auth.resolver import CredentialStores
from bitbucket_unofficial_cli.commands import annotation
from bitbucket_unofficial_cli.commands import auth
from bitbucket_unofficial_cli.commands import branch
from bitbucket_unofficial_cli.commands import branch_restriction
from bitbucket_unofficial_cli.commands import branching_model
from bitbucket_unofficial_cli.commands import commit
from bitbucket_unofficial_cli.commands import config
from bitbucket_unofficial_cli.commands import default_reviewer
from bitbucket_unofficial_cli.commands import deploy_key
from bitbucket_unofficial_cli.commands import deployment
from bitbucket_unofficial_cli.commands import download
from bitbucket_unofficial_cli.commands import environment
from bitbucket_unofficial_cli.commands import hook_event
from bitbucket_unofficial_cli.commands import member
from bitbucket_unofficial_cli.commands import permission
from bitbucket_unofficial_cli.commands import permission_config
from bitbucket_unofficial_cli.commands import pipeline
from bitbucket_unofficial_cli.commands import pr
from bitbucket_unofficial_cli.commands import project
from bitbucket_unofficial_cli.commands import ref
from bitbucket_unofficial_cli.commands import repo
from bitbucket_unofficial_cli.commands import report
from bitbucket_unofficial_cli.commands import search
from bitbucket_unofficial_cli.commands import snippet
from bitbucket_unofficial_cli.commands import source
from bitbucket_unofficial_cli.commands import tag
from bitbucket_unofficial_cli.commands import team
from bitbucket_unofficial_cli.commands import user
from bitbucket_unofficial_cli.commands import webhook
from bitbucket_unofficial_cli.commands import workspace
from bitbucket_unofficial_cli.config.paths import credentials_file
from bitbucket_unofficial_cli.config.paths import settings_file
from bitbucket_unofficial_cli.config.settings import GlobalOptions
from bitbucket_unofficial_cli.config.settings import OutputFormat
from bitbucket_unofficial_cli.config.settings import resolve_options
from bitbucket_unofficial_cli.config.store import SettingsStore
from bitbucket_unofficial_cli.output.registry import create_renderer
from bitbucket_unofficial_cli.output.renderer import RenderTarget
from bitbucket_unofficial_cli.runtime.client_factory import create_sdk_client
from bitbucket_unofficial_cli.runtime.context import AppContext
from bitbucket_unofficial_cli.runtime.context import Services
from bitbucket_unofficial_cli.runtime.errors import handle_errors
from bitbucket_unofficial_cli.runtime.params import options_from

if TYPE_CHECKING:
    from collections.abc import Callable


def default_services() -> Services:
    return Services(
        settings=SettingsStore(settings_file()),
        credentials=CredentialStores(
            environment=EnvCredentialStore(os.environ),
            keyring=KeyringCredentialStore(),
            file=FileCredentialStore(credentials_file()),
        ),
        clients=create_sdk_client,
        oauth=OAuthClient(),
        open_browser=webbrowser.open,
    )


def print_version(
    value: bool,  # ruff: ignore[boolean-type-hint-positional-argument]  Typer passes the flag value positionally
) -> None:
    if value:
        typer.echo(f"bitbucket {__version__}")
        raise typer.Exit


@dataclass(frozen=True, slots=True)
class _RootOptions:
    profile: Annotated[
        str | None,
        typer.Option("--profile", "-p", envvar="BITBUCKET_PROFILE", help="Configuration profile to use."),
    ] = None
    workspace: Annotated[
        str | None,
        typer.Option("--workspace", "-w", envvar="BITBUCKET_WORKSPACE", help="Workspace slug; overrides the profile."),
    ] = None
    output: Annotated[
        OutputFormat | None,
        typer.Option("--output", "-o", envvar="BITBUCKET_OUTPUT", case_sensitive=False, help="Output format."),
    ] = None
    verbose: Annotated[
        bool,
        typer.Option("--verbose", "-v", help="Print HTTP request diagnostics to stderr."),
    ] = False
    version: Annotated[
        bool,
        typer.Option("--version", callback=print_version, is_eager=True, help="Show the version and exit."),
    ] = False


# Global options must precede the sub-command (`bitbucket -o json auth status`). Colors follow
# Rich's NO_COLOR handling, so there is no --no-color flag to keep the callback small.
def create_app(services_factory: Callable[[], Services] = default_services) -> typer.Typer:
    cli = typer.Typer(
        name="bitbucket",
        help="Unofficial command-line interface for Bitbucket Cloud.",
        no_args_is_help=True,
    )

    @cli.callback()
    @handle_errors
    @options_from(_RootOptions)
    def root(ctx: typer.Context, options: _RootOptions) -> None:
        flags = GlobalOptions(
            profile=options.profile, workspace=options.workspace, output=options.output, verbose=options.verbose
        )
        _bind_context(ctx=ctx, services=services_factory(), flags=flags)

    def _bind_context(*, ctx: typer.Context, services: Services, flags: GlobalOptions) -> None:
        resolved = resolve_options(flags, services.settings.load(), is_tty=sys.stdout.isatty())
        console = Console(highlight=False)
        renderer = create_renderer(resolved.output, RenderTarget(console=console, stream=sys.stdout))
        app_context = AppContext(options=resolved, services=services, console=console, renderer=renderer)
        ctx.obj = app_context
        ctx.call_on_close(app_context.close)

    cli.add_typer(auth.APP, name="auth")
    cli.add_typer(config.APP, name="config")
    cli.add_typer(user.APP, name="user")
    cli.add_typer(workspace.APP, name="workspace")
    cli.add_typer(repo.APP, name="repo")
    cli.add_typer(project.APP, name="project")
    cli.add_typer(pr.APP, name="pr")
    cli.add_typer(commit.APP, name="commit")
    cli.add_typer(branch.APP, name="branch")
    cli.add_typer(tag.APP, name="tag")
    cli.add_typer(ref.APP, name="ref")
    cli.add_typer(source.APP, name="source")
    cli.add_typer(report.APP, name="report")
    cli.add_typer(annotation.APP, name="annotation")
    cli.add_typer(download.APP, name="download")
    cli.add_typer(branch_restriction.APP, name="branch-restriction")
    cli.add_typer(branching_model.APP, name="branching-model")
    cli.add_typer(default_reviewer.APP, name="default-reviewer")
    cli.add_typer(deploy_key.APP, name="deploy-key")
    cli.add_typer(permission_config.APP, name="permission-config")
    cli.add_typer(pipeline.APP, name="pipeline")
    cli.add_typer(environment.APP, name="environment")
    cli.add_typer(deployment.APP, name="deployment")
    cli.add_typer(snippet.APP, name="snippet")
    cli.add_typer(team.APP, name="team")
    cli.add_typer(search.APP, name="search")
    cli.add_typer(member.APP, name="member")
    cli.add_typer(permission.APP, name="permission")
    cli.add_typer(webhook.APP, name="webhook")
    cli.add_typer(hook_event.APP, name="hook-event")
    return cli


APP: Final = create_app()


def run() -> None:
    APP(prog_name="bitbucket")

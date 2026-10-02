from dataclasses import dataclass
from pathlib import Path
from typing import Annotated
from typing import Final

import typer

from bitbucket_unofficial_cli.output.columns import DOWNLOADS
from bitbucket_unofficial_cli.output.renderer import many
from bitbucket_unofficial_cli.runtime.context import get_app_context
from bitbucket_unofficial_cli.runtime.errors import CliError
from bitbucket_unofficial_cli.runtime.errors import handle_errors
from bitbucket_unofficial_cli.runtime.exit_codes import ExitCode
from bitbucket_unofficial_cli.runtime.params import PagingOptions
from bitbucket_unofficial_cli.runtime.params import Repo
from bitbucket_unofficial_cli.runtime.params import Yes
from bitbucket_unofficial_cli.runtime.params import options_from
from bitbucket_unofficial_cli.services.listing import paged

APP: Final = typer.Typer(help="Manage the downloadable files of a repository.", no_args_is_help=True)

Filename = Annotated[str, typer.Argument(help="Name of the download.")]  # pylint: disable=gajaguar-module-const-naming,gajaguar-require-final


@dataclass(frozen=True, slots=True, kw_only=True)
class _ListOptions(PagingOptions):
    repo: Repo


@APP.command(name="list", help="List the downloads of a repository.")
@handle_errors
@options_from(_ListOptions)
def list_downloads(ctx: typer.Context, options: _ListOptions) -> None:
    app_context = get_app_context(ctx)
    downloads = app_context.repository(options.repo).downloads
    found = paged(app_context, options, downloads.list, downloads.list_page)
    app_context.render(many(found, DOWNLOADS, id_key="name"))


@APP.command(help="Fetch a download to stdout, or save it with --output-file.")
@handle_errors
def get(
    ctx: typer.Context,
    filename: Filename,
    repo: Repo,
    output_file: Annotated[Path | None, typer.Option("--output-file", help="Write the file here.")] = None,
) -> None:
    app_context = get_app_context(ctx)
    content = app_context.repository(repo).downloads.get(filename)
    if output_file is None:
        app_context.write_bytes(content)
    else:
        output_file.write_bytes(content)
        app_context.notify(f"Wrote {len(content)} bytes to {output_file}.")


@APP.command(help="Upload a file to the downloads.")
@handle_errors
def upload(
    ctx: typer.Context,
    file: Annotated[Path, typer.Argument(help="Local file to upload.")],
    repo: Repo,
    name: Annotated[str | None, typer.Option("--name", help="Name to store it as; defaults to the file name.")] = None,
) -> None:
    app_context = get_app_context(ctx)
    try:
        content = file.read_bytes()
    except OSError as error:
        message = f"Cannot read {file}: {error}"
        raise CliError(message, exit_code=ExitCode.USAGE) from error
    stored = name or file.name
    app_context.repository(repo).downloads.upload(stored, content)
    app_context.notify(f"Uploaded '{stored}'.")


@APP.command(help="Delete a download.")
@handle_errors
def delete(ctx: typer.Context, filename: Filename, repo: Repo, *, yes: Yes = False) -> None:
    app_context = get_app_context(ctx)
    app_context.confirm(f"Delete download '{filename}'?", assume_yes=yes)
    app_context.repository(repo).downloads.delete(filename)
    app_context.notify(f"Deleted download '{filename}'.")

from dataclasses import dataclass
from pathlib import Path
from typing import Annotated
from typing import Final

import typer

from bitbucket_unofficial_cli.output.columns import FILE_HISTORY
from bitbucket_unofficial_cli.output.columns import TREE
from bitbucket_unofficial_cli.output.renderer import many
from bitbucket_unofficial_cli.runtime.context import get_app_context
from bitbucket_unofficial_cli.runtime.errors import CliError
from bitbucket_unofficial_cli.runtime.errors import handle_errors
from bitbucket_unofficial_cli.runtime.exit_codes import ExitCode
from bitbucket_unofficial_cli.runtime.params import PagingOptions
from bitbucket_unofficial_cli.runtime.params import Repo
from bitbucket_unofficial_cli.runtime.params import options_from
from bitbucket_unofficial_cli.services.files import read_local_files
from bitbucket_unofficial_cli.services.listing import paged

APP: Final = typer.Typer(help="Browse and commit repository source.", no_args_is_help=True)

Rev = Annotated[str, typer.Argument(help="Commit hash, branch or tag.")]  # pylint: disable=gajaguar-module-const-naming,gajaguar-require-final
FilePath = Annotated[str, typer.Argument(help="Path of the file in the repository.")]  # pylint: disable=gajaguar-module-const-naming,gajaguar-require-final


@dataclass(frozen=True, slots=True, kw_only=True)
class _ListOptions(PagingOptions):
    repo: Repo
    path: Annotated[str | None, typer.Argument(help="Directory to list; defaults to the root.")] = None
    rev: Annotated[str | None, typer.Option("--rev", help="Commit, branch or tag; defaults to the main branch.")] = (
        None
    )


@dataclass(frozen=True, slots=True, kw_only=True)
class _HistoryOptions(PagingOptions):
    repo: Repo
    rev: Rev
    path: FilePath


@dataclass(frozen=True, slots=True, kw_only=True)
class _CommitOptions:
    repo: Repo
    files: Annotated[
        list[str],
        typer.Option("--file", help="LOCAL or LOCAL:REMOTE file to commit; repeatable."),
    ]
    message: Annotated[str | None, typer.Option("--message", "-m", help="Commit message.")] = None
    branch: Annotated[str | None, typer.Option("--branch", help="Branch to commit to.")] = None
    author: Annotated[str | None, typer.Option("--author", help="Author as 'Name <email>'.")] = None


@APP.command(name="ls", help="List a directory of the repository.")
@handle_errors
@options_from(_ListOptions)
def list_directory(ctx: typer.Context, options: _ListOptions) -> None:
    app_context = get_app_context(ctx)
    source = app_context.repository(options.repo).source
    rev = options.rev
    if rev is None:
        if options.path:
            message = "--rev is required to list a path."
            raise CliError(message, exit_code=ExitCode.USAGE)
        found = paged(app_context, options, source.list, source.list_page)
    else:
        path = options.path or ""
        found = paged(
            app_context,
            options,
            lambda: source.list_path(rev, path),
            lambda **page: source.list_path_page(rev, path, **page),
        )
    app_context.render(many(found, TREE, id_key="path"))


@APP.command(help="Print a file, or save it with --output-file.")
@handle_errors
def cat(
    ctx: typer.Context,
    rev: Rev,
    path: FilePath,
    repo: Repo,
    output_file: Annotated[Path | None, typer.Option("--output-file", help="Write the file here.")] = None,
) -> None:
    app_context = get_app_context(ctx)
    content = app_context.repository(repo).source.read(rev, path)
    if output_file is None:
        app_context.write_bytes(content)
    else:
        output_file.write_bytes(content)
        app_context.notify(f"Wrote {len(content)} bytes to {output_file}.")


@APP.command(help="List the commits that changed a file.")
@handle_errors
@options_from(_HistoryOptions)
def history(ctx: typer.Context, options: _HistoryOptions) -> None:
    app_context = get_app_context(ctx)
    source = app_context.repository(options.repo).source
    found = paged(
        app_context,
        options,
        lambda: source.file_history(options.rev, options.path),
        lambda **page: source.file_history_page(options.rev, options.path, **page),
    )
    app_context.render(many(found, FILE_HISTORY, id_key="commit.hash"))


@APP.command(help="Commit local files to a branch.")
@handle_errors
@options_from(_CommitOptions)
def commit(ctx: typer.Context, options: _CommitOptions) -> None:
    app_context = get_app_context(ctx)
    files = read_local_files(options.files)
    source = app_context.repository(options.repo).source
    source.create_commit(files, message=options.message, branch=options.branch, author=options.author)
    app_context.notify(f"Committed {len(files)} file(s).")

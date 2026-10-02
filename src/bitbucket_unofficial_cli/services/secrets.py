from __future__ import annotations

import os
import sys
from typing import TYPE_CHECKING

import typer

from bitbucket_unofficial_cli.runtime.errors import CliError
from bitbucket_unofficial_cli.runtime.exit_codes import ExitCode

if TYPE_CHECKING:
    from pathlib import Path


def _interactive() -> bool:
    return sys.stdin.isatty()


# A secret never travels as a command-line argument, where it would land in shell history and `ps`.
# It comes from stdin, or from a hidden prompt on a terminal.
def read_secret(label: str, *, from_stdin: bool) -> str:
    if from_stdin:
        return sys.stdin.read().rstrip("\r\n")
    if _interactive():
        return str(typer.prompt(label, hide_input=True, err=True))
    message = f"Cannot ask for the {label} without a terminal."
    raise CliError(message, exit_code=ExitCode.USAGE, hint="Pass --stdin and pipe the value in.")


def read_secret_file(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError as error:
        message = f"Cannot read {path}: {error}"
        raise CliError(message, exit_code=ExitCode.USAGE) from error


# A variable named on the command line takes its value from the environment of the same name.
def value_from_environment(name: str) -> str:
    value = os.environ.get(name)
    if value is None:
        message = f"The environment variable {name} is not set."
        raise CliError(message, exit_code=ExitCode.USAGE)
    return value


__all__ = ["read_secret", "read_secret_file", "value_from_environment"]

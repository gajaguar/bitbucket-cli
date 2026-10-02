from __future__ import annotations

from pathlib import Path

from bitbucket_unofficial_cli.runtime.errors import CliError
from bitbucket_unofficial_cli.runtime.exit_codes import ExitCode


# `LOCAL` uploads a file under its own path; `LOCAL:REMOTE` stores it under another one.
def read_local_files(specs: list[str]) -> dict[str, bytes]:
    files: dict[str, bytes] = {}
    for spec in specs:
        local, _, remote = spec.partition(":")
        try:
            files[remote or local] = Path(local).read_bytes()
        except OSError as error:
            message = f"Cannot read {local}: {error}"
            raise CliError(message, exit_code=ExitCode.USAGE) from error
    return files


__all__ = ["read_local_files"]

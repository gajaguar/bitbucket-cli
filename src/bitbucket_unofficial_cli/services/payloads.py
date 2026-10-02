from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from pydantic import ValidationError

from bitbucket_unofficial_cli.runtime.errors import CliError
from bitbucket_unofficial_cli.runtime.exit_codes import ExitCode

if TYPE_CHECKING:
    from bitbucket.models.base import BitbucketModel


def _read(source: str) -> object:
    try:
        text = sys.stdin.read() if source == "-" else Path(source).read_text(encoding="utf-8")
        return json.loads(text)
    except (OSError, ValueError) as error:
        message = f"Cannot read a JSON body from {source!r}: {error}"
        raise CliError(message, exit_code=ExitCode.USAGE) from error


# Flags left at None are unset, so only what the caller named reaches the wire (the SDK dumps with
# exclude_unset); a flag wins over the same field in --from-file.
def build[T: BitbucketModel](model: type[T], source: str | None = None, /, **fields: object) -> T:
    body: dict[str, object] = {}
    if source is not None:
        loaded = _read(source)
        if not isinstance(loaded, dict):
            message = "The JSON body must be an object."
            raise CliError(message, exit_code=ExitCode.USAGE)
        body.update(loaded)
    body.update({name: value for name, value in fields.items() if value is not None})
    try:
        return model.model_validate(body)
    except ValidationError as error:
        message = f"Invalid {model.__name__}: {error}"
        raise CliError(message, exit_code=ExitCode.USAGE) from error


# For bulk uploads: --from-file holds a JSON array of bodies.
def build_many[T: BitbucketModel](model: type[T], source: str) -> list[T]:
    loaded = _read(source)
    if not isinstance(loaded, list):
        message = "The JSON body must be an array."
        raise CliError(message, exit_code=ExitCode.USAGE)
    try:
        return [model.model_validate(item) for item in loaded]
    except ValidationError as error:
        message = f"Invalid {model.__name__}: {error}"
        raise CliError(message, exit_code=ExitCode.USAGE) from error


__all__ = ["build", "build_many"]

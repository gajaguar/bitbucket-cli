from __future__ import annotations

import json
import sys
from typing import TYPE_CHECKING

from bitbucket_unofficial_cli.runtime.errors import CliError
from bitbucket_unofficial_cli.runtime.exit_codes import ExitCode

if TYPE_CHECKING:
    from bitbucket._transport import JSONValue


# A property value is any JSON, so it is parsed here instead of being modelled; "-" reads stdin.
def parse_value(text: str) -> JSONValue:
    raw = sys.stdin.read() if text == "-" else text
    try:
        return json.loads(raw)  # type: ignore[no-any-return]
    except ValueError as error:
        message = f"The value is not valid JSON: {error}"
        raise CliError(message, exit_code=ExitCode.USAGE) from error


__all__ = ["parse_value"]

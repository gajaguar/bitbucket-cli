from __future__ import annotations

import tomllib
from tempfile import NamedTemporaryFile
from typing import TYPE_CHECKING
from typing import Final

import tomli_w
from pydantic import ValidationError

from bitbucket_unofficial_cli.config.settings import Settings
from bitbucket_unofficial_cli.runtime.errors import CliError
from bitbucket_unofficial_cli.runtime.exit_codes import ExitCode

if TYPE_CHECKING:
    from pathlib import Path

PRIVATE_FILE_MODE: Final = 0o600
PRIVATE_DIR_MODE: Final = 0o700


def read_toml(path: Path) -> dict[str, object]:
    try:
        with path.open("rb") as handle:
            return tomllib.load(handle)
    except FileNotFoundError:
        return {}
    except tomllib.TOMLDecodeError as error:
        message = f"Cannot parse {path}: {error}"
        raise CliError(message, exit_code=ExitCode.CONFIGURATION) from error


# Written to a sibling temp file and renamed so a crash never leaves a half-written file,
# and created 0600 from the start so secrets are never briefly world-readable.
def write_private_toml(path: Path, data: dict[str, object]) -> None:
    path.parent.mkdir(mode=PRIVATE_DIR_MODE, parents=True, exist_ok=True)
    with NamedTemporaryFile("wb", dir=path.parent, prefix=f".{path.name}.", delete=False) as handle:
        tomli_w.dump(data, handle)
    temp_path = path.parent / handle.name
    temp_path.chmod(PRIVATE_FILE_MODE)
    temp_path.replace(path)


class SettingsStore:
    def __init__(self, path: Path) -> None:
        self.path = path

    def load(self) -> Settings:
        try:
            return Settings.model_validate(read_toml(self.path))
        except ValidationError as error:
            message = f"Invalid settings in {self.path}: {error.error_count()} problem(s)"
            raise CliError(message, exit_code=ExitCode.CONFIGURATION, hint=str(error)) from error

    def save(self, settings: Settings) -> None:
        write_private_toml(self.path, settings.model_dump(mode="json", exclude_none=True))

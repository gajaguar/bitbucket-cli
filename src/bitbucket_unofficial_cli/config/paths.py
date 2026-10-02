from __future__ import annotations

from os import environ
from pathlib import Path
from typing import Final

from platformdirs import user_config_path

APP_NAME: Final = "bitbucket-cli"
CONFIG_DIR_ENV_VAR: Final = "BITBUCKET_CLI_CONFIG_DIR"


def config_dir() -> Path:
    override = environ.get(CONFIG_DIR_ENV_VAR)
    if override:
        return Path(override)
    return user_config_path(APP_NAME)


def settings_file() -> Path:
    return config_dir() / "config.toml"


def credentials_file() -> Path:
    return config_dir() / "credentials.toml"

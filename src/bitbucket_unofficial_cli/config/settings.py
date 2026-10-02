from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Final

from pydantic import BaseModel
from pydantic import ConfigDict

DEFAULT_PROFILE: Final = "default"


class OutputFormat(StrEnum):
    TABLE = "table"
    JSON = "json"
    JSONL = "jsonl"
    CSV = "csv"
    ID = "id"


class Profile(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    workspace: str | None = None
    account_id: str | None = None
    display_name: str | None = None


class Settings(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    default_profile: str = DEFAULT_PROFILE
    output: OutputFormat | None = None
    profiles: dict[str, Profile] = {}

    def with_profile(self, name: str, profile: Profile) -> Settings:
        return self.model_copy(update={"profiles": {**self.profiles, name: profile}})

    def without_profile(self, name: str) -> Settings:
        remaining = {key: value for key, value in self.profiles.items() if key != name}
        return self.model_copy(update={"profiles": remaining})


# Flag and environment values arrive already merged by Typer (flag wins over envvar).
@dataclass(frozen=True, slots=True)
class GlobalOptions:
    profile: str | None = None
    workspace: str | None = None
    output: OutputFormat | None = None
    verbose: bool = False


@dataclass(frozen=True, slots=True)
class ResolvedOptions:
    profile_name: str
    profile: Profile
    workspace: str | None
    output: OutputFormat
    verbose: bool


def resolve_options(options: GlobalOptions, settings: Settings, *, is_tty: bool) -> ResolvedOptions:
    profile_name = options.profile or settings.default_profile
    profile = settings.profiles.get(profile_name, Profile())
    # Humans get tables; pipes get machine-readable JSON unless something explicit says otherwise.
    fallback_output = OutputFormat.TABLE if is_tty else OutputFormat.JSON
    return ResolvedOptions(
        profile_name=profile_name,
        profile=profile,
        workspace=options.workspace or profile.workspace,
        output=options.output or settings.output or fallback_output,
        verbose=options.verbose,
    )

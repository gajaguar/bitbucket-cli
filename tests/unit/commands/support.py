from __future__ import annotations

import json
from typing import TYPE_CHECKING
from typing import Final

import httpx

from tests.conftest import BASE_URL

if TYPE_CHECKING:
    from typer import Typer
    from typer.testing import CliRunner
    from typer.testing import Result

TOKEN_ENV: Final = {"ATLASSIAN_USER_EMAIL": "me@example.com", "ATLASSIAN_API_TOKEN": "tok"}
REPOS: Final = f"{BASE_URL}/repositories/acme"
WORKSPACE: Final = f"{BASE_URL}/workspaces/acme"


def page(values: list[dict[str, object]], *, next_url: str | None = None) -> httpx.Response:
    body: dict[str, object] = {"values": values, "pagelen": 10}
    if next_url:
        body["next"] = next_url
    return httpx.Response(200, json=body)


def run(
    cli: Typer,
    runner: CliRunner,
    environ: dict[str, str],
    *args: str,
    stdin: str | None = None,
    output: str = "json",
) -> Result:
    environ.update(TOKEN_ENV)
    environ.setdefault("BITBUCKET_WORKSPACE", "acme")
    return runner.invoke(cli, ["-w", "acme", "-o", output, *args], input=stdin)


def body_of(request: httpx.Request) -> dict[str, object]:
    return json.loads(request.content)

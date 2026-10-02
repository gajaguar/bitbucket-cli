from __future__ import annotations

import json
from typing import TYPE_CHECKING
from typing import Final

import httpx
import respx

from bitbucket_unofficial_cli.config.settings import Profile
from bitbucket_unofficial_cli.runtime.exit_codes import ExitCode
from tests.conftest import BASE_URL
from tests.conftest import REPOSITORY_PAYLOAD
from tests.conftest import USER_PAYLOAD
from tests.conftest import WORKSPACE_PAYLOAD

if TYPE_CHECKING:
    from typer import Typer
    from typer.testing import CliRunner

    from bitbucket_unofficial_cli.runtime.context import Services

TOKEN_ENV: Final = {"ATLASSIAN_USER_EMAIL": "me@example.com", "ATLASSIAN_API_TOKEN": "tok"}
ACCESS: Final = {"workspace": WORKSPACE_PAYLOAD, "administrator": True, "type": "workspace_access"}


def page(values: list[dict[str, object]], *, next_url: str | None = None) -> httpx.Response:
    body: dict[str, object] = {"values": values, "pagelen": 10}
    if next_url:
        body["next"] = next_url
    return httpx.Response(200, json=body)


@respx.mock
def test_user_me_renders_the_user(cli: Typer, runner: CliRunner, environ: dict[str, str]) -> None:
    # Arrange
    environ.update(TOKEN_ENV)
    respx.get(f"{BASE_URL}/user").mock(return_value=httpx.Response(200, json=USER_PAYLOAD))
    # Act
    result = runner.invoke(cli, ["-o", "json", "user", "me"])
    # Assert
    assert result.exit_code == ExitCode.OK
    assert json.loads(result.stdout)["account_id"] == "557058:abc"


@respx.mock
def test_user_me_as_an_id_prints_the_account_id(cli: Typer, runner: CliRunner, environ: dict[str, str]) -> None:
    # Arrange
    environ.update(TOKEN_ENV)
    respx.get(f"{BASE_URL}/user").mock(return_value=httpx.Response(200, json=USER_PAYLOAD))
    # Act
    result = runner.invoke(cli, ["-o", "id", "user", "me"])
    # Assert
    assert result.stdout == "557058:abc\n"


@respx.mock
def test_workspace_list_flattens_the_access_records(cli: Typer, runner: CliRunner, environ: dict[str, str]) -> None:
    # Arrange
    environ.update(TOKEN_ENV)
    route = respx.get(f"{BASE_URL}/user/workspaces").mock(return_value=page([ACCESS]))
    # Act
    result = runner.invoke(cli, ["-o", "csv", "workspace", "list", "--administrator"])
    # Assert
    assert result.stdout.splitlines() == ["Slug,Name,Private,Admin", "acme,Acme,yes,yes"]
    assert route.calls.last.request.url.params["administrator"] == "true"


@respx.mock
def test_workspace_list_as_ids_prints_slugs(cli: Typer, runner: CliRunner, environ: dict[str, str]) -> None:
    # Arrange
    environ.update(TOKEN_ENV)
    respx.get(f"{BASE_URL}/user/workspaces").mock(return_value=page([ACCESS]))
    # Act
    result = runner.invoke(cli, ["-o", "id", "workspace", "list"])
    # Assert
    assert result.stdout == "acme\n"


@respx.mock
def test_workspace_list_prints_the_next_cursor_for_a_single_page(
    cli: Typer, runner: CliRunner, environ: dict[str, str]
) -> None:
    # Arrange
    environ.update(TOKEN_ENV)
    second = f"{BASE_URL}/user/workspaces?page=2"
    respx.get(f"{BASE_URL}/user/workspaces", params={"page": "2"}).mock(return_value=page([ACCESS]))
    # Act
    result = runner.invoke(cli, ["-o", "id", "workspace", "list", "--cursor", second])
    # Assert
    assert result.exit_code == ExitCode.OK
    assert result.stdout == "acme\n"
    assert "next cursor" not in result.stderr


@respx.mock
def test_a_cursor_run_reports_where_to_continue(cli: Typer, runner: CliRunner, environ: dict[str, str]) -> None:
    # Arrange
    environ.update(TOKEN_ENV)
    cursor = f"{BASE_URL}/user/workspaces?page=2"
    following = f"{BASE_URL}/user/workspaces?page=3"
    respx.get(cursor).mock(return_value=page([ACCESS], next_url=following))
    # Act
    result = runner.invoke(cli, ["-o", "id", "workspace", "list", "--cursor", cursor])
    # Assert
    assert f"next cursor: {following}" in result.stderr


def test_limit_and_cursor_cannot_be_combined(cli: Typer, runner: CliRunner, environ: dict[str, str]) -> None:
    # Arrange
    environ.update(TOKEN_ENV)
    # Act
    result = runner.invoke(cli, ["workspace", "list", "--limit", "1", "--cursor", "https://x"])
    # Assert
    assert result.exit_code == ExitCode.USAGE


@respx.mock
def test_limit_stops_after_n_rows_without_fetching_more(
    cli: Typer, runner: CliRunner, environ: dict[str, str]
) -> None:
    # Arrange
    environ.update(TOKEN_ENV)
    other = {**REPOSITORY_PAYLOAD, "slug": "gadgets", "full_name": "acme/gadgets"}
    respx.get(f"{BASE_URL}/repositories/acme").mock(
        return_value=page([REPOSITORY_PAYLOAD, other], next_url=f"{BASE_URL}/repositories/acme?page=2")
    )
    # Act
    result = runner.invoke(cli, ["-o", "id", "-w", "acme", "repo", "list", "--limit", "1"])
    # Assert
    assert result.stdout == "widgets\n"


@respx.mock
def test_repo_list_follows_the_next_links_and_passes_filters(
    cli: Typer, runner: CliRunner, environ: dict[str, str]
) -> None:
    # Arrange
    environ.update(TOKEN_ENV)
    other = {**REPOSITORY_PAYLOAD, "slug": "gadgets", "full_name": "acme/gadgets"}
    first = respx.get(f"{BASE_URL}/repositories/acme", params={"q": "is_private=true", "sort": "name"}).mock(
        return_value=page([REPOSITORY_PAYLOAD], next_url=f"{BASE_URL}/repositories/acme?page=2")
    )
    respx.get(f"{BASE_URL}/repositories/acme?page=2").mock(return_value=page([other]))
    # Act
    result = runner.invoke(cli, ["-o", "id", "-w", "acme", "repo", "list", "-q", "is_private=true", "--sort", "name"])
    # Assert
    assert result.stdout == "widgets\ngadgets\n"
    assert first.called


@respx.mock
def test_repo_list_renders_a_table_for_a_terminal(cli: Typer, runner: CliRunner, environ: dict[str, str]) -> None:
    # Arrange
    environ.update(TOKEN_ENV)
    respx.get(f"{BASE_URL}/repositories/acme").mock(return_value=page([REPOSITORY_PAYLOAD]))
    # Act
    result = runner.invoke(cli, ["-o", "table", "-w", "acme", "repo", "list"])
    # Assert
    assert "acme/widgets" in result.stdout
    assert "main" in result.stdout


@respx.mock
def test_repo_get_renders_one_repository(cli: Typer, runner: CliRunner, environ: dict[str, str]) -> None:
    # Arrange
    environ.update(TOKEN_ENV)
    respx.get(f"{BASE_URL}/repositories/acme/widgets").mock(return_value=httpx.Response(200, json=REPOSITORY_PAYLOAD))
    # Act
    result = runner.invoke(cli, ["-o", "json", "-w", "acme", "repo", "get", "widgets"])
    # Assert
    assert json.loads(result.stdout)["full_name"] == "acme/widgets"


def test_a_workspace_command_without_a_workspace_explains_how_to_select_one(
    cli: Typer, runner: CliRunner, environ: dict[str, str]
) -> None:
    # Arrange
    environ.update(TOKEN_ENV)
    # Act
    result = runner.invoke(cli, ["repo", "list"])
    # Assert
    assert result.exit_code == ExitCode.CONFIGURATION
    assert "workspace use" in result.stderr


@respx.mock
def test_the_profile_workspace_is_used_when_no_flag_is_given(
    cli: Typer, runner: CliRunner, services: Services, environ: dict[str, str]
) -> None:
    # Arrange
    environ.update(TOKEN_ENV)
    services.settings.save(services.settings.load().with_profile("default", Profile(workspace="acme")))
    route = respx.get(f"{BASE_URL}/repositories/acme").mock(return_value=page([]))
    # Act
    result = runner.invoke(cli, ["-o", "json", "repo", "list"])
    # Assert
    assert result.exit_code == ExitCode.OK
    assert route.called


@respx.mock
def test_workspace_get_defaults_to_the_selected_workspace(
    cli: Typer, runner: CliRunner, environ: dict[str, str]
) -> None:
    # Arrange
    environ.update(TOKEN_ENV)
    respx.get(f"{BASE_URL}/workspaces/acme").mock(return_value=httpx.Response(200, json=WORKSPACE_PAYLOAD))
    # Act
    selected = runner.invoke(cli, ["-o", "json", "-w", "acme", "workspace", "get"])
    explicit = runner.invoke(cli, ["-o", "json", "workspace", "get", "acme"])
    # Assert
    assert json.loads(selected.stdout)["slug"] == "acme"
    assert json.loads(explicit.stdout)["slug"] == "acme"


@respx.mock
def test_workspace_use_validates_then_saves_the_choice(
    cli: Typer, runner: CliRunner, services: Services, environ: dict[str, str]
) -> None:
    # Arrange
    environ.update(TOKEN_ENV)
    services.settings.save(services.settings.load().with_profile("default", Profile()))
    respx.get(f"{BASE_URL}/workspaces/acme").mock(return_value=httpx.Response(200, json=WORKSPACE_PAYLOAD))
    # Act
    result = runner.invoke(cli, ["workspace", "use", "acme"])
    # Assert
    assert result.exit_code == ExitCode.OK
    assert services.settings.load().profiles["default"].workspace == "acme"


@respx.mock
def test_workspace_use_needs_an_existing_profile(cli: Typer, runner: CliRunner, environ: dict[str, str]) -> None:
    # Arrange
    environ.update(TOKEN_ENV)
    respx.get(f"{BASE_URL}/workspaces/acme").mock(return_value=httpx.Response(200, json=WORKSPACE_PAYLOAD))
    # Act
    result = runner.invoke(cli, ["workspace", "use", "acme"])
    # Assert
    assert result.exit_code == ExitCode.CONFIGURATION


@respx.mock
def test_an_unknown_workspace_is_not_found(cli: Typer, runner: CliRunner, environ: dict[str, str]) -> None:
    # Arrange
    environ.update(TOKEN_ENV)
    respx.get(f"{BASE_URL}/workspaces/nope").mock(
        return_value=httpx.Response(404, json={"type": "error", "error": {"message": "No workspace"}})
    )
    # Act
    result = runner.invoke(cli, ["workspace", "use", "nope"])
    # Assert
    assert result.exit_code == ExitCode.NOT_FOUND
    assert "HTTP 404" in result.stderr


@respx.mock
def test_verbose_logs_each_request_to_stderr(cli: Typer, runner: CliRunner, environ: dict[str, str]) -> None:
    # Arrange
    environ.update(TOKEN_ENV)
    respx.get(f"{BASE_URL}/user").mock(return_value=httpx.Response(200, json=USER_PAYLOAD))
    # Act
    result = runner.invoke(cli, ["-v", "-o", "json", "user", "me"])
    # Assert
    assert result.exit_code == ExitCode.OK
    assert "GET" not in result.stdout


def test_config_path_list_and_use(cli: Typer, runner: CliRunner, services: Services) -> None:
    # Arrange
    settings = services.settings.load().with_profile("work", Profile(workspace="acme", display_name="Some One"))
    services.settings.save(settings.with_profile("home", Profile()))
    # Act
    path = runner.invoke(cli, ["config", "path"])
    listing = runner.invoke(cli, ["-o", "json", "config", "list"])
    use = runner.invoke(cli, ["config", "use", "work"])
    unknown = runner.invoke(cli, ["config", "use", "nope"])
    # Assert
    assert path.stdout.strip() == str(services.settings.path)
    assert [row["name"] for row in json.loads(listing.stdout)] == ["home", "work"]
    assert use.exit_code == ExitCode.OK
    assert services.settings.load().default_profile == "work"
    assert unknown.exit_code == ExitCode.CONFIGURATION

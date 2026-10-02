from __future__ import annotations

import os
import socket
import threading
import urllib.parse
import urllib.request
from typing import TYPE_CHECKING
from typing import Final
from urllib.parse import parse_qs
from urllib.parse import urlparse

import httpx
import keyring
import pytest
from bitbucket import NO_RETRY
from bitbucket import ClientOptions
from keyring.backend import KeyringBackend
from keyring.errors import PasswordDeleteError
from typer.testing import CliRunner

from bitbucket_unofficial_cli.auth.env_store import EnvCredentialStore
from bitbucket_unofficial_cli.auth.file_store import FileCredentialStore
from bitbucket_unofficial_cli.auth.keyring_store import KeyringCredentialStore
from bitbucket_unofficial_cli.auth.oauth import OAuthClient
from bitbucket_unofficial_cli.auth.resolver import CredentialStores
from bitbucket_unofficial_cli.config.store import SettingsStore
from bitbucket_unofficial_cli.main import create_app
from bitbucket_unofficial_cli.runtime.client_factory import build_client
from bitbucket_unofficial_cli.runtime.context import Services

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path

    import typer
    from bitbucket import BitbucketClient

    from bitbucket_unofficial_cli.runtime.client_factory import ClientRequest


BASE_URL: Final = "https://fake.bitbucket.test/2.0"
NOW: Final = 1_000_000.0

USER_PAYLOAD: Final = {
    "type": "user",
    "uuid": "{11111111-1111-1111-1111-111111111111}",
    "display_name": "Some One",
    "nickname": "someone",
    "account_id": "557058:abc",
    "account_status": "active",
}

WORKSPACE_PAYLOAD: Final = {
    "type": "workspace",
    "uuid": "{22222222-2222-2222-2222-222222222222}",
    "name": "Acme",
    "slug": "acme",
    "is_private": True,
    "created_on": "2024-01-02T03:04:05.000000+00:00",
}

REPOSITORY_PAYLOAD: Final = {
    "type": "repository",
    "uuid": "{33333333-3333-3333-3333-333333333333}",
    "full_name": "acme/widgets",
    "name": "Widgets",
    "slug": "widgets",
    "is_private": True,
    "language": "python",
    "scm": "git",
    "mainbranch": {"type": "branch", "name": "main"},
    "project": {"type": "project", "key": "WID"},
    "owner": {"type": "team", "display_name": "Acme"},
}


class MemoryKeyring(KeyringBackend):
    priority = 1

    def __init__(self) -> None:
        super().__init__()
        self.passwords: dict[tuple[str, str], str] = {}

    def get_password(self, service: str, username: str) -> str | None:
        return self.passwords.get((service, username))

    def set_password(self, service: str, username: str, password: str) -> None:
        self.passwords[service, username] = password

    def delete_password(self, service: str, username: str) -> None:
        if (service, username) not in self.passwords:
            raise PasswordDeleteError(username)
        del self.passwords[service, username]


def fake_client(request: ClientRequest) -> BitbucketClient:
    return build_client(request, ClientOptions(base_url=BASE_URL, retry=NO_RETRY))


def get_free_port() -> int:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return int(probe.getsockname()[1])


# Stands in for the user's browser: instead of opening the authorize URL it calls the local callback,
# echoing the `state` Bitbucket would echo, the way the real redirect does.
class FakeBrowser:
    def __init__(self, port: int) -> None:
        self.port = port
        self.urls: list[str] = []
        self.code: str | None = "the-code"
        self.state: str | None = None
        self.error: str | None = None
        self.silent = False
        self.threads: list[threading.Thread] = []

    def __call__(self, url: str) -> bool:
        self.urls.append(url)
        if self.silent:
            return True
        state = self.state if self.state is not None else parse_qs(urlparse(url).query)["state"][0]
        query = {"state": state}
        if self.code:
            query["code"] = self.code
        if self.error:
            query["error"] = self.error
        target = f"http://127.0.0.1:{self.port}/callback?{urllib.parse.urlencode(query)}"
        thread = threading.Thread(target=lambda: urllib.request.urlopen(target, timeout=10).read())
        thread.start()
        self.threads.append(thread)
        return True


# The developer's own credentials must never reach a test: Typer, the SDK and the env store all read these.
# Typer forces ANSI styling when GITHUB_ACTIONS is set, which splits an option name in the help text.
@pytest.fixture(autouse=True)  # ruff: ignore[pytest-fixture-autouse]  every test must start without real credentials
def clean_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in list(os.environ):
        if name.startswith(("ATLASSIAN_", "BITBUCKET_")):
            monkeypatch.delenv(name)
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)


@pytest.fixture(name="memory_keyring")
def memory_keyring_fixture() -> Iterator[MemoryKeyring]:
    previous = keyring.get_keyring()
    backend = MemoryKeyring()
    keyring.set_keyring(backend)
    yield backend
    keyring.set_keyring(previous)


@pytest.fixture(name="environ")
def environ_fixture() -> dict[str, str]:
    return {}


@pytest.fixture(name="oauth")
def oauth_fixture() -> OAuthClient:
    return OAuthClient(http=httpx.Client, clock=lambda: NOW)


@pytest.fixture(name="browser")
def browser_fixture() -> FakeBrowser:
    return FakeBrowser(get_free_port())


@pytest.fixture(name="services")
def services_fixture(
    tmp_path: Path,
    memory_keyring: MemoryKeyring,
    environ: dict[str, str],
    oauth: OAuthClient,
    browser: FakeBrowser,
) -> Services:
    del memory_keyring
    return Services(
        settings=SettingsStore(tmp_path / "config.toml"),
        credentials=CredentialStores(
            environment=EnvCredentialStore(environ),
            keyring=KeyringCredentialStore(),
            file=FileCredentialStore(tmp_path / "credentials.toml"),
        ),
        clients=fake_client,
        oauth=oauth,
        open_browser=browser,
    )


@pytest.fixture
def cli(services: Services) -> typer.Typer:
    return create_app(lambda: services)


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()

from __future__ import annotations

import time
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler
from http.server import HTTPServer
from typing import Final
from typing import cast
from typing import override
from urllib.parse import parse_qs
from urllib.parse import urlparse

from bitbucket_unofficial_cli.runtime.errors import CliError
from bitbucket_unofficial_cli.runtime.exit_codes import ExitCode

LOOPBACK: Final = "127.0.0.1"
CALLBACK_PATH: Final = "/callback"
DEFAULT_PORT: Final = 8976
_PAGE: Final = b"<html><body><p>Bitbucket CLI: you can close this tab and return to the terminal.</p></body></html>"


@dataclass(frozen=True, slots=True)
class CallbackResult:
    code: str | None = None
    state: str | None = None
    error: str | None = None


def parse_redirect(url: str) -> CallbackResult:
    query = parse_qs(urlparse(url).query)

    def first(name: str) -> str | None:
        values = query.get(name)
        return values[0] if values else None

    return CallbackResult(code=first("code"), state=first("state"), error=first("error_description") or first("error"))


class _Server(HTTPServer):
    result: CallbackResult | None = None


class _Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if urlparse(self.path).path != CALLBACK_PATH:
            self.send_error(404)
            return
        # HTTPServer types the attribute as its base class; this handler is only ever built by _Server.
        cast("_Server", self.server).result = parse_redirect(self.path)
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(_PAGE)))
        self.end_headers()
        self.wfile.write(_PAGE)

    # Keeps the terminal clean: the CLI reports its own progress.
    @override
    def log_message(self, format: str, *args: object) -> None:
        del format, args


# Bound to the loopback interface only, and it serves just the one callback request.
class CallbackServer:
    def __init__(self, port: int = DEFAULT_PORT) -> None:
        try:
            self._server = _Server((LOOPBACK, port), _Handler)
        except OSError as error:
            message = f"Cannot listen on {LOOPBACK}:{port}: {error}"
            raise CliError(
                message,
                exit_code=ExitCode.CONFIGURATION,
                hint="Pick another port with --callback-port, or use --no-browser.",
            ) from error

    @property
    def port(self) -> int:
        return int(self._server.server_address[1])

    def wait(self, timeout: float) -> CallbackResult:
        deadline = time.monotonic() + timeout
        while self._server.result is None:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                message = "Timed out waiting for the browser to return to the callback URL."
                raise CliError(message, exit_code=ExitCode.AUTHENTICATION, hint="Retry, or use --no-browser.")
            self._server.timeout = remaining
            self._server.handle_request()
        return self._server.result

    def close(self) -> None:
        self._server.server_close()

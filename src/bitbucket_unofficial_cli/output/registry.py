from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Final

from bitbucket_unofficial_cli.config.settings import OutputFormat
from bitbucket_unofficial_cli.output.formats import CsvRenderer
from bitbucket_unofficial_cli.output.formats import IdRenderer
from bitbucket_unofficial_cli.output.formats import JsonLinesRenderer
from bitbucket_unofficial_cli.output.formats import JsonRenderer
from bitbucket_unofficial_cli.output.formats import TableRenderer

if TYPE_CHECKING:
    from collections.abc import Callable

    from bitbucket_unofficial_cli.output.renderer import RenderTarget
    from bitbucket_unofficial_cli.output.renderer import Renderer

_RENDERERS: Final[dict[OutputFormat, Callable[[RenderTarget], Renderer]]] = {
    OutputFormat.TABLE: TableRenderer,
    OutputFormat.JSON: JsonRenderer,
    OutputFormat.JSONL: JsonLinesRenderer,
    OutputFormat.CSV: CsvRenderer,
    OutputFormat.ID: IdRenderer,
}


def create_renderer(output: OutputFormat, target: RenderTarget) -> Renderer:
    return _RENDERERS[output](target)

from __future__ import annotations

import csv
import json
from typing import TYPE_CHECKING

from rich.table import Table

from bitbucket_unofficial_cli.output.renderer import Column

if TYPE_CHECKING:
    from bitbucket_unofficial_cli.output.renderer import Dataset
    from bitbucket_unofficial_cli.output.renderer import RenderTarget


def _cell(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, (dict, list)):
        return json.dumps(value)
    return str(value)


class TableRenderer:
    def __init__(self, target: RenderTarget) -> None:
        self._console = target.console

    def render(self, dataset: Dataset) -> None:
        if dataset.single and dataset.records:
            table = Table(show_header=False, box=None)
            table.add_column(style="bold")
            table.add_column()
            for column in dataset.columns:
                table.add_row(column.header, _cell(column.value(dataset.records[0])))
        else:
            table = Table()
            for column in dataset.columns:
                table.add_column(column.header)
            for record in dataset.records:
                table.add_row(*(_cell(column.value(record)) for column in dataset.columns))
        self._console.print(table)


class JsonRenderer:
    def __init__(self, target: RenderTarget) -> None:
        self._stream = target.stream

    def render(self, dataset: Dataset) -> None:
        payload = dataset.records[0] if dataset.single and dataset.records else list(dataset.records)
        self._stream.write(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")


class JsonLinesRenderer:
    def __init__(self, target: RenderTarget) -> None:
        self._stream = target.stream

    def render(self, dataset: Dataset) -> None:
        for record in dataset.records:
            self._stream.write(json.dumps(record, ensure_ascii=False) + "\n")


class CsvRenderer:
    def __init__(self, target: RenderTarget) -> None:
        self._stream = target.stream

    def render(self, dataset: Dataset) -> None:
        writer = csv.writer(self._stream, lineterminator="\n")
        writer.writerow(column.header for column in dataset.columns)
        for record in dataset.records:
            writer.writerow(_cell(column.value(record)) for column in dataset.columns)


# Bare identifiers, one per line, for `xargs`/`$(...)` pipelines.
class IdRenderer:
    def __init__(self, target: RenderTarget) -> None:
        self._stream = target.stream

    def render(self, dataset: Dataset) -> None:
        key = Column(dataset.id_key, "")
        for record in dataset.records:
            identifier = key.value(record)
            if identifier is not None:
                self._stream.write(f"{identifier}\n")

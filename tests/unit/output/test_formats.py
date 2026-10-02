from __future__ import annotations

import io
import json
from typing import Final

import pytest
from pydantic import BaseModel
from rich.console import Console

from bitbucket_unofficial_cli.config.settings import OutputFormat
from bitbucket_unofficial_cli.output.registry import create_renderer
from bitbucket_unofficial_cli.output.renderer import Column
from bitbucket_unofficial_cli.output.renderer import RenderTarget
from bitbucket_unofficial_cli.output.renderer import many
from bitbucket_unofficial_cli.output.renderer import single
from bitbucket_unofficial_cli.output.renderer import to_record

COLUMNS: Final = (
    Column("slug", "Slug"),
    Column("meta.owner", "Owner"),
    Column("private", "Private"),
    Column("tags", "Tags"),
)
RECORDS: Final = [
    {"slug": "a", "meta": {"owner": "me"}, "private": True, "tags": ["x"], "uuid": "{1}"},
    {"slug": "b", "meta": None, "private": False, "tags": None, "uuid": "{2}"},
]


class Item(BaseModel):
    full_name: str


FIRST: Final = RECORDS[0]


def render(output: OutputFormat, dataset: object) -> str:
    stream = io.StringIO()
    console = Console(file=stream, width=200, highlight=False, force_terminal=False)
    create_renderer(output, RenderTarget(console=console, stream=stream)).render(dataset)  # type: ignore[arg-type]
    return stream.getvalue()


def test_json_renders_a_list_or_a_single_object() -> None:
    # Arrange
    # Act
    listed = json.loads(render(OutputFormat.JSON, many(RECORDS, COLUMNS)))
    one = json.loads(render(OutputFormat.JSON, single(RECORDS[0], COLUMNS)))
    # Assert
    assert [row["slug"] for row in listed] == ["a", "b"]
    assert one == FIRST


def test_jsonl_renders_one_record_per_line() -> None:
    # Arrange
    # Act
    lines = render(OutputFormat.JSONL, many(RECORDS, COLUMNS)).splitlines()
    # Assert
    assert [json.loads(line)["slug"] for line in lines] == ["a", "b"]


def test_csv_flattens_nested_values_and_booleans() -> None:
    # Arrange
    # Act
    lines = render(OutputFormat.CSV, many(RECORDS, COLUMNS)).splitlines()
    # Assert
    assert lines == ["Slug,Owner,Private,Tags", 'a,me,yes,"[""x""]"', "b,,no,"]


def test_table_renders_headers_and_a_key_value_view_for_one_record() -> None:
    # Arrange
    # Act
    table = render(OutputFormat.TABLE, many(RECORDS, COLUMNS))
    detail = render(OutputFormat.TABLE, single(RECORDS[0], COLUMNS))
    # Assert
    assert "Slug" in table
    assert "me" in table
    assert "Owner" in detail
    assert "Slug" in detail


@pytest.mark.parametrize(("id_key", "expected"), [("uuid", "{1}\n{2}\n"), ("meta.owner", "me\n")])
def test_id_prints_the_chosen_identifier_and_skips_missing_ones(id_key: str, expected: str) -> None:
    # Arrange
    dataset = many(RECORDS, COLUMNS, id_key=id_key)
    # Act
    output = render(OutputFormat.ID, dataset)
    # Assert
    assert output == expected


def test_to_record_dumps_models_and_rejects_other_objects() -> None:
    # Arrange
    # Act
    record = to_record(Item(full_name="acme/widgets"))
    # Assert
    assert record == {"full_name": "acme/widgets"}
    assert to_record({"a": 1}) == {"a": 1}
    with pytest.raises(TypeError):
        to_record(42)

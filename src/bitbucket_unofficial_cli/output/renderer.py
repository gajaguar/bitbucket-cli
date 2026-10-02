from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from dataclasses import field
from typing import TYPE_CHECKING
from typing import Final
from typing import Protocol

from pydantic import BaseModel

if TYPE_CHECKING:
    from collections.abc import Iterable
    from collections.abc import Sequence
    from typing import TextIO

    from rich.console import Console

type Record = Mapping[str, object]  # pylint: disable=gajaguar-module-const-naming

DEFAULT_ID_KEY: Final = "uuid"


@dataclass(frozen=True, slots=True)
class Column:
    key: str
    header: str

    # Keys may be dotted paths into nested API objects, e.g. "mainbranch.name".
    def value(self, record: Record) -> object:
        current: object = record
        for part in self.key.split("."):
            if not isinstance(current, Mapping):
                return None
            current = current.get(part)
        return current


# id_key names the field the `id` format prints; Bitbucket has no uniform `id`, so each
# resource picks the identifier a script would pass back (a slug, an account id, a UUID).
@dataclass(frozen=True, slots=True)
class Dataset:
    records: Sequence[Record]
    columns: Sequence[Column]
    single: bool = False
    id_key: str = DEFAULT_ID_KEY


@dataclass(frozen=True, slots=True)
class RenderTarget:
    console: Console
    stream: TextIO = field(repr=False)


class Renderer(Protocol):
    def render(self, dataset: Dataset) -> None: ...


# JSON output keeps Bitbucket's snake_case field names so it lines up with the API docs.
def to_record(item: BaseModel | Record | object) -> Record:
    if isinstance(item, BaseModel):
        return item.model_dump(mode="json", by_alias=True)
    if isinstance(item, Mapping):
        return item
    message = f"Cannot coerce {type(item).__name__} to a renderer record."
    raise TypeError(message)


def many(
    items: Iterable[BaseModel | Record],
    columns: Sequence[Column],
    *,
    id_key: str = DEFAULT_ID_KEY,
) -> Dataset:
    return Dataset(records=[to_record(item) for item in items], columns=columns, id_key=id_key)


def single(item: BaseModel | Record, columns: Sequence[Column], *, id_key: str = DEFAULT_ID_KEY) -> Dataset:
    return Dataset(records=[to_record(item)], columns=columns, single=True, id_key=id_key)

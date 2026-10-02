from __future__ import annotations

import itertools
from dataclasses import dataclass
from typing import TYPE_CHECKING

from bitbucket_unofficial_cli.runtime.errors import CliError
from bitbucket_unofficial_cli.runtime.exit_codes import ExitCode

if TYPE_CHECKING:
    from collections.abc import Callable
    from collections.abc import Iterable
    from collections.abc import Iterator

    from bitbucket._pagination import Page

    from bitbucket_unofficial_cli.runtime.context import AppContext
    from bitbucket_unofficial_cli.runtime.params import PagingOptions


@dataclass(frozen=True, slots=True)
class ListOptions:
    limit: int | None = None
    cursor: str | None = None


# Bitbucket pages by cursor (the `next` URL), so there is no page number to jump to: either walk
# lazily from the start, or fetch the single page a previous run printed.
def collect[T](
    fetch_all: Callable[[], Iterator[T]],
    fetch_page: Callable[..., Page[T]],
    options: ListOptions,
    *,
    on_next: Callable[[str], None],
) -> Iterable[T]:
    if options.cursor is not None:
        if options.limit is not None:
            message = "--limit cannot be combined with --cursor."
            raise CliError(message, exit_code=ExitCode.USAGE)
        page = fetch_page(cursor=options.cursor)
        if page.next_cursor:
            on_next(page.next_cursor)
        return page.items
    if options.limit is None:
        return fetch_all()
    return itertools.islice(fetch_all(), options.limit)


# NestedResource.list takes only set values, so unset filters are dropped before the call.
def filters(**values: str | None) -> dict[str, str]:
    return {name: value for name, value in values.items() if value is not None}


# The common shape of a list command: stream every item, or fetch the page a cursor names.
def paged[T](
    app_context: AppContext,
    options: PagingOptions,
    fetch_all: Callable[[], Iterator[T]],
    fetch_page: Callable[..., Page[T]],
) -> Iterable[T]:
    return collect(
        fetch_all,
        fetch_page,
        ListOptions(limit=options.limit, cursor=options.cursor),
        on_next=lambda cursor: app_context.notify(f"next cursor: {cursor}"),
    )


__all__ = ["ListOptions", "collect", "filters", "paged"]

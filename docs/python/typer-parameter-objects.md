---
type: rule
title: Typer parameter objects
description: A command with more options than the argument limit declares them as a frozen dataclass and decorates the command with options_from.
tags: [python, typer]
status: stable
---

# Typer parameter objects

Typer builds a command from the callback's signature, so every option has to
be a function parameter. A command with six or more options therefore trips
`too-many-arguments`, which is better solved than silenced.

`runtime/params.py` provides `options_from(cls)`. The options live in a frozen,
`slots=True` dataclass, each field declared with
`Annotated[..., typer.Option(...)]` or `typer.Argument(...)`. The decorator
rebuilds the signature Typer reads from the dataclass fields, then calls the
command with `(ctx, options)`:

```python
@dataclass(frozen=True, slots=True)
class _CreateOptions:
    name: Annotated[str, typer.Option("--name", help="Display name.")]
    note: Annotated[str | None, typer.Option("--note")] = None


@APP.command(help="Create a thing.")
@handle_errors
@options_from(_CreateOptions)
def create(ctx: typer.Context, options: _CreateOptions) -> None: ...
```

Rules:

- Order the decorators `@APP.command`, `@handle_errors`, `@options_from`.
- Fields without a default come first, as in any dataclass; an argument goes
  first, then the options.
- Fields are keyword-only for Typer, so a field that would shadow a builtin is
  renamed (`field_type` with `--type`).
- Use it from six options up; a shorter signature stays a plain function.

Options shared by several commands live in a base dataclass that each command's
dataclass extends; `options_from` reads the annotations of the whole class
hierarchy.

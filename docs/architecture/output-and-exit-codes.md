---
type: rule
title: Output formats, streams and exit codes
description: Which formats the CLI prints, which stream carries what, and the frozen exit codes scripts can rely on.
tags: [architecture, output]
status: stable
---

# Output formats, streams and exit codes

## Formats

`--output` (`-o`, `BITBUCKET_OUTPUT`) selects one of five formats.

| Format  | Prints                                                                     |
| ------- | -------------------------------------------------------------------------- |
| `table` | A table, or a key and value list for one record. The default on a terminal |
| `json`  | A list, or an object for one record. The default when stdout is not a tty  |
| `jsonl` | One JSON object per line                                                   |
| `csv`   | A header row and one row per record, with the table's columns              |
| `id`    | One bare identifier per line, for `xargs` and `$(...)`                     |

The order of precedence is the flag or environment variable, then `output` in
`config.toml`, then the terminal check.

JSON keeps Bitbucket's own `snake_case` field names, so a record lines up with
the API documentation. Table and CSV use the columns in `output/columns.py`,
whose keys can be dotted paths such as `mainbranch.name`.

Bitbucket has no uniform `id`. Each dataset names the field the `id` format
prints: the slug for a repository or workspace, the account ID for a user.

## Streams

- Rendered data goes to stdout.
- Prompts, notices, the next-page cursor and errors go to stderr.

## Exit codes

| Code | Name             | Raised for                                               |
| ---- | ---------------- | -------------------------------------------------------- |
| 0    | `OK`             | Success                                                  |
| 1    | `FAILURE`        | Anything not listed below                                |
| 2    | `USAGE`          | A bad combination of options                             |
| 3    | `CONFIGURATION`  | No credential, no workspace, an unreadable settings file |
| 4    | `AUTHENTICATION` | A rejected credential, or an OAuth exchange that failed  |
| 5    | `FORBIDDEN`      | HTTP 403                                                 |
| 6    | `NOT_FOUND`      | HTTP 404                                                 |
| 7    | `VALIDATION`     | HTTP 400, 409 or 422                                     |
| 8    | `RATE_LIMITED`   | HTTP 429 after the SDK's retries                         |
| 9    | `UNAVAILABLE`    | HTTP 5xx, a network failure, or a polling timeout        |

Codes 1 and 2 belong to Click. A new failure class gets a new code; no code is
ever renumbered.

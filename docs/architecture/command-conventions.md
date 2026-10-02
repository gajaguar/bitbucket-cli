---
type: rule
title: Command conventions
description: The options and output rules every write, delete and repository-scoped command shares.
tags: [architecture, cli]
status: stable
---

# Command conventions

## Repository scope

A command that works inside one repository takes `--repo` (`-r`), which reads
`BITBUCKET_REPOSITORY`. The workspace comes from the global `--workspace`.
`repo` commands take the slug as an argument instead, since the repository is
their subject. `webhook` takes `--repo` as optional: without it the command
acts on the workspace.

## Deleting

A command that deletes or removes something asks first. `--yes` (`-y`) skips
the question. Without a terminal and without `--yes` the command exits with
`USAGE` and changes nothing, so a script never hangs on a prompt.

## Request bodies

A command that creates or updates something takes the common fields as flags.
`--from-file FILE` reads the whole body as JSON, with `-` for stdin, for the
fields no flag covers. A flag overrides the same field in the file. Only the
fields named by a flag or the file are sent.

## Raw text

A diff, a patch, a log or a key is not a dataset. It is written to stdout
as it is, whatever `--output` says, and ends with a newline.

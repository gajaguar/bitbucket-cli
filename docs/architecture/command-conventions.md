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

Settings that exist on a repository and on a project (`branching-model`,
`default-reviewer`, `deploy-key`, `permission-config`) take `--repo` or
`--project`. An explicit `--repo` together with `--project` is a usage error;
a `BITBUCKET_REPOSITORY` from the environment gives way to `--project`.

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

## Secrets

A secret is never an argument and is never printed. A variable value comes
from a hidden prompt on a terminal, or from stdin with `--stdin`. A private
key comes from `--private-key-file` or stdin. A pipeline run takes variables
from the environment with `--variable-env NAME`. The SDK masks every secret
field it returns, and the output keeps the mask. The OAuth credentials Bitbucket
returns when it registers a runner are masked too, so a runner that needs them
is registered in the Bitbucket UI.

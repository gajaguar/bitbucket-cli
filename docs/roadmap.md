---
type: playbook
title: Roadmap
description: The releases that take the CLI from the 0.1.0 scaffold to 1.0.0, when it exposes every capability of bitbucket-unofficial-sdk.
tags: [roadmap]
status: draft
---

# Roadmap

`1.0.0` exposes **every capability that `bitbucket-unofficial-sdk` offers**.
[`coverage.md`](coverage.md) lists each SDK resource with the command that
wraps it, the release that adds it and its status. The CLI is done when every
row is `done`.

The SDK is the source of truth. The CLI wraps the synchronous client only: the
async client mirrors it one to one, so it adds no capability a command line
needs. The three Bitbucket `Addon` operations are outside the SDK, because they
need JWT or Forge authentication, so they are outside the CLI too.

## Releases to 1.0.0

Each release adds one area. The CLI follows
[SemVer](conventions/versioning.md): before `1.0.0` a new command group is a
minor release, and each minor release gets a Git tag. A release that only fixes
a bug is a patch and is tagged only when it is published.

| Release | Area                                                                                                                                               |
| ------- | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| `0.1.0` | Foundation: API token, access token and OAuth login; profiles; output formats; `user me`; workspace and repository read commands                   |
| `0.2.0` | Repositories (create, update, delete, forks, watchers), projects, workspace members and permissions, webhooks, hook events                         |
| `0.3.0` | Pull requests: create, update, approve, request changes, decline, merge, diff, comments, tasks, statuses, activity, conflicts, mergeability checks |
| `0.4.0` | Branches, tags, commits, source browsing and commits, commit statuses, reports and annotations, downloads                                          |
| `0.5.0` | Branch restrictions, branching model, default reviewers, deploy keys, repository and project permissions, properties                               |
| `0.6.0` | Pipelines (run, stop, steps, logs, test reports) and their configuration: variables, schedules, known hosts, SSH key pair, caches, runners, OIDC   |
| `0.7.0` | Environments, deployment variables and deployments                                                                                                 |
| `0.8.0` | User SSH and GPG keys, emails, user and team pipeline variables, code search                                                                       |
| `0.9.0` | Snippets: create, update, files, revisions, commits, diff, comments, watching                                                                      |
| `1.0.0` | Stability: the contracts below are frozen. No new capability                                                                                       |

Code search is deprecated by Bitbucket on 2026-11-01. It ships in `0.8.0` for
as long as the SDK keeps it, and a later release removes it with the SDK.

## What 1.0.0 freezes

From `1.0.0` a breaking change needs a major version. The contract is:

- **Exit codes.** The values in
  [Output formats, streams and exit codes](architecture/output-and-exit-codes.md).
  A new failure gets a new code; none is renumbered.
- **JSON output.** `-o json` and `jsonl` keep Bitbucket's field names. Removing
  or renaming a field, or changing its type, is breaking; adding one is not.
  The `id` and `csv` formats keep their shape.
- **Streams.** Rendered data goes to stdout. Prompts, notices and errors go to
  stderr.
- **Command surface.** The `bitbucket <noun> <verb>` grammar, the commands and
  options in `coverage.md` that are `done`, the global options with their
  environment variables, and the keys of `config.toml`.

The table layout, column headers, message text and `--help` are not frozen.

## Cross-repo workflow

A command the SDK cannot back waits for the SDK. Add the method to
`bitbucket-sdk`, release it, raise the SDK floor in `pyproject.toml`, and then
add the command here. If the SDK change is breaking, the CLI follows its
major version.

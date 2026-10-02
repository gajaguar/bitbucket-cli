---
name: bitbucket-cli
description: >-
  Operate the bitbucket CLI beyond pull requests and pipelines: authentication
  and profiles, workspaces, members and permissions, projects, repositories,
  branches, tags, commits and their statuses, source browsing, reports,
  downloads, branch restrictions, branching model, default reviewers, deploy
  keys, webhooks, snippets and user keys. Use when the user says "bitbucket
  login", "switch workspace", "list repos", "create a repository", "create a
  branch", "show a file at a revision", "list commits", "add a webhook",
  "protect a branch", "add a deploy key", "create a snippet", or asks how to
  use the bitbucket command.
license: MIT
compatibility: Requires the bitbucket CLI (bitbucket-unofficial-cli, Python 3.14+) and a logged-in Bitbucket credential
allowed-tools: Bash Read AskUserQuestion
---

# Bitbucket CLI

Reference for driving the `bitbucket` CLI. For pull requests use the
`bitbucket-pull-requests` skill; for pipelines, environments and deployments,
the `bitbucket-pipelines` skill.

## Rules

- Global options MUST come before the subcommand: `-p/--profile`,
  `-w/--workspace`, `-o/--output` (`table|json|jsonl|csv|id`), `-v/--verbose`.
  They also read `BITBUCKET_PROFILE`, `BITBUCKET_WORKSPACE` and
  `BITBUCKET_OUTPUT`.
- MUST pass `-o json` (or `-o id`) when parsing output. Data goes to stdout,
  diagnostics and the next-page cursor to stderr.
- A command inside one repository takes `--repo/-r SLUG` (or
  `BITBUCKET_REPOSITORY`); `repo` commands take the slug as an argument. The
  settings that exist on a repository and on a project (`branching-model`,
  `default-reviewer`, `deploy-key`, `permission-config`) take `--repo` or
  `--project`, never both.
- Lists take `--limit N`, or `--cursor URL` for one page.
- Fields without a flag go through `--from-file FILE` (or `-` for stdin) as
  JSON; a flag overrides the same field in the file.
- Secrets MUST NOT be passed as arguments or printed. MUST NOT run `bitbucket
  auth token` unless the user explicitly asks for the raw token.
- Anything that deletes or removes MUST be confirmed with the user through
  `AskUserQuestion` first; pass `--yes` only after that. Without `--yes` and
  without a terminal the command exits with code 2 and changes nothing.
- Diffs, patches, logs, file contents and keys are raw text on stdout,
  whatever `-o` says.

## Instructions

1. MUST run `bitbucket --version`. If it is missing, recommend `uv tool
   install bitbucket-unofficial-cli` or `pipx install bitbucket-unofficial-cli`
   and stop.
2. Authentication and profiles:
   - `bitbucket auth login` (Atlassian email and API token), `--access-token`
     or `--oauth` are interactive (hidden prompt): the user runs them, not the
     agent. In CI the credential comes from `ATLASSIAN_USER_EMAIL` with
     `ATLASSIAN_API_TOKEN`, or from `BITBUCKET_ACCESS_TOKEN`.
   - `bitbucket -o json auth status` shows the credential and its user; exit
     code 3 or 4 means the user must log in. `auth refresh` renews an OAuth
     token and `auth logout` removes the credential.
   - `bitbucket config path|list` and `config use NAME` inspect and select
     profiles.
3. Workspace: `workspace list|get|use` (`use SLUG` persists the choice in the
   active profile), `workspace gpg-key`, `oidc-configuration`, `oidc-keys`.
   Without a workspace, commands exit with code 3.
4. Resource management, each with `bitbucket <group> <verb> --help`:

   | Group                   | Verbs                                                                                                         |
   | ----------------------- | ------------------------------------------------------------------------------------------------------------- |
   | `user`                  | `me`, `get`; `user email`, `ssh-key`, `gpg-key`, `variable`                                                   |
   | `member`, `permission`  | `list`, `get`; `permission mine`                                                                              |
   | `project`               | list, get, create, update, delete                                                                             |
   | `repo`                  | list, get, create, update, delete, fork, forks, watchers; `repo property`                                     |
   | `branch`, `tag`         | list, get, create, delete                                                                                     |
   | `ref`                   | list                                                                                                          |
   | `commit`                | list, get, diff, diffstat, patch, merge-base, prs, approve, unapprove; `commit comment`, `status`, `property` |
   | `source`                | `ls`, `cat REV PATH`, `history`, `commit`                                                                     |
   | `report`, `annotation`  | code-insights reports and annotations                                                                         |
   | `download`              | list, get, upload, delete                                                                                     |
   | `branch-restriction`    | list, get, create, update, delete                                                                             |
   | `branching-model`       | get, effective, settings, update                                                                              |
   | `default-reviewer`      | list, get, effective, add, remove                                                                             |
   | `deploy-key`            | list, get, create, update, delete                                                                             |
   | `permission-config`     | `user`, `group`, `override` access to a repository or project                                                 |
   | `webhook`, `hook-event` | list, get, create, update, delete; events a webhook can subscribe to                                          |
   | `snippet`               | list, get, create, update, delete, file, diff, patch, commits, watch; `snippet comment`, `revision`           |
   | `team variable`         | list, get, create, update, delete                                                                             |
   | `search code`           | code search; Bitbucket deprecates it on 2026-11-01                                                            |

   `webhook` takes `--repo` as optional: without it the command acts on the
   workspace. A variable value comes from a hidden prompt or `--stdin`; a
   private key from `--private-key-file` or stdin.

   Read with `list`/`get` first to confirm the target before `update` or
   `delete`.
5. If a repository, branch or other resource is not found (exit code 6), list
   the candidates and ask the user which one they meant.
6. On any other non-zero exit, follow [exit-codes.md](references/exit-codes.md).

Only the commands in `bitbucket --help` exist; the SDK capabilities behind
them are listed in the project's `docs/coverage.md`.

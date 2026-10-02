---
name: bitbucket-pull-requests
description: >-
  Work with Bitbucket Cloud pull requests through the bitbucket CLI: list,
  open, update, review, comment on, approve, decline and merge them, and manage
  their tasks and build statuses. Use when the user says "open a PR", "create
  a pull request", "list my pull requests", "review PR 12", "comment on the
  PR", "approve", "request changes", "merge the PR", "is the PR mergeable",
  or gives a Bitbucket pull request number.
license: MIT
compatibility: Requires the bitbucket CLI (bitbucket-unofficial-cli, Python 3.14+) and a logged-in Bitbucket credential
allowed-tools: Bash Read AskUserQuestion
---

# Bitbucket pull requests

Drive the `bitbucket pr` commands. The CLI owns authentication, paging and
output formatting; this skill only chooses the right command and flags. For
repositories, branches, commits and everything else, use the `bitbucket-cli`
skill; for builds, the `bitbucket-pipelines` skill.

## Rules

- Global options (`-p`, `-w`, `-o`, `-v`) MUST come before the subcommand:
  `bitbucket -o json pr list -r my-repo`, never `bitbucket pr list -o json`.
  They also read `BITBUCKET_PROFILE`, `BITBUCKET_WORKSPACE` and
  `BITBUCKET_OUTPUT`.
- MUST pass `-o json` (or `-o id`) whenever the output is parsed. Data is on
  stdout; notices and the next-page cursor are on stderr.
- Every `pr` command takes `--repo/-r SLUG` (or `BITBUCKET_REPOSITORY`). The
  pull request is a positional ID: `bitbucket pr get 12 -r my-repo`.
- Lists take `--limit N`, or `--cursor URL` for one page.
- MUST NOT ask for, print or pass credentials, and MUST NOT run `bitbucket
  auth token`. The user logs in themselves.
- `pr diff` and `pr patch` print raw text whatever `-o` says; do not parse
  them as JSON.
- Fields without a flag go through `--from-file FILE` (or `-` for stdin) as
  JSON; a flag overrides the same field in the file.
- Reviewers are passed as UUIDs with a repeatable `--reviewer`.

## Instructions

1. MUST run `bitbucket --version`. If it is missing, recommend `uv tool
   install bitbucket-unofficial-cli` or `pipx install bitbucket-unofficial-cli`
   and stop.
2. MUST run `bitbucket -o json auth status`. On exit code 3 or 4, tell the
   user to run `bitbucket auth login` (interactive, hidden prompt) and stop.
3. Choose the workflow:

   | Goal               | Command                                                                                                                 |
   | ------------------ | ----------------------------------------------------------------------------------------------------------------------- |
   | List pull requests | `bitbucket -o json pr list -r REPO [--state OPEN] [--query Q] [--sort -updated_on] [--limit N]`                         |
   | By author          | `bitbucket -o json pr by-author USER_ID`                                                                                |
   | Show one           | `bitbucket -o json pr get ID -r REPO`                                                                                   |
   | Open one           | `bitbucket pr create -r REPO --title T --source BRANCH --destination BRANCH [--description D] [--reviewer UUID]`        |
   | Edit one           | `bitbucket pr update ID -r REPO [--title] [--description] ...`                                                          |
   | Read the change    | `pr files`, `pr commits`, `pr diff`, `pr patch`, `pr activity` (all `ID -r REPO`)                                       |
   | Review             | `pr approve`, `pr unapprove`, `pr request-changes`, `pr unrequest-changes`                                              |
   | Comment            | `pr comment create ID -r REPO -m TEXT [--inline-path F --inline-to N] [--parent CID]`                                   |
   | Resolve a thread   | `pr comment resolve ID COMMENT -r REPO` (and `unresolve`; `list`, `get`, `update`, `delete`)                            |
   | Tasks              | `pr task create ID -r REPO -m TEXT`, plus `list`, `get`, `update`, `delete`                                             |
   | Build statuses     | `pr status list ID -r REPO`                                                                                             |
   | Can it merge?      | `pr checks ID`, `pr conflicts ID` (both with `-r REPO`)                                                                 |
   | Merge              | `bitbucket pr merge ID -r REPO [--strategy merge_commit/squash/fast_forward] [-m MSG] [--close-source-branch] [--wait]` |
   | Decline            | `bitbucket pr decline ID -r REPO`                                                                                       |

4. To open a pull request from the current checkout, take the repository slug
   from the user (or `git remote get-url origin`), the source from `git branch
   --show-current` and the destination from the user; MUST confirm the title
   and destination before running `pr create`.
5. To review, read `pr get`, `pr files` and `pr diff` first, then comment
   (inline with `--inline-path` and `--inline-to`), and approve or request
   changes only when the user asks for that verdict.
6. Before `pr merge`, MUST run `pr checks` and `pr conflicts`,
   report any problem, and MUST ask the user with `AskUserQuestion` to
   confirm the merge and its strategy. The same goes for `pr decline` and for
   any `delete`, which takes `--yes` only after the user agreed. `--wait`
   makes `pr merge` wait for the merge to finish.
7. If a repository or pull request is not found (exit code 6), run
   `bitbucket -o json repo list` or `pr list` and ask which one the user meant.
8. On any other non-zero exit, follow [exit-codes.md](references/exit-codes.md).

Run `bitbucket pr <command> --help` for flags not listed here.

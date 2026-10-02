---
type: reference
title: SDK coverage
description: Each capability of bitbucket-unofficial-sdk, the CLI command that wraps it, the release that adds it and its status.
tags: [roadmap, sdk]
status: draft
---

# SDK coverage

Every capability of `bitbucket-unofficial-sdk` 1.0.1, grouped by SDK resource.
`1.0.0` needs every row `done`. The notation is:

- **SDK** gives the access path: `ws` is a `WorkspaceClient`, `repo` a
  `RepositoryClient`, `project` a `ProjectClient`, `snippet` a `SnippetClient`.
  A resource with `create`, `get`, `list`, `update` and `delete` is written as
  *CRUD*.
- **CLI command** is the command that exposes it. For a `planned` row it is the
  proposed name, which can still change before it ships.
- **Release** is the CLI release that adds it; see [`roadmap.md`](roadmap.md).
- **Status** is `done` or `planned`.

## Account and workspace

| SDK                                                               | CLI command                                | Release | Status |
| ----------------------------------------------------------------- | ------------------------------------------ | ------- | ------ |
| `client.user.me()`                                                | `bitbucket user me`                        | 0.1.0   | done   |
| `client.user.workspaces()`                                        | `bitbucket workspace list`                 | 0.1.0   | done   |
| `ws.get()`                                                        | `bitbucket workspace get`                  | 0.1.0   | done   |
| `ws.members` list, get                                            | `bitbucket member list`, `get`             | 0.2.0   | done   |
| `ws.my_permission()`, `ws.my_repository_permissions()`            | `bitbucket permission mine`                | 0.2.0   | done   |
| `ws.permissions` list, repositories, repository                   | `bitbucket permission list`                | 0.2.0   | done   |
| `ws.gpg_public_key()`                                             | `bitbucket workspace gpg-key`              | 0.2.0   | done   |
| `ws.pull_requests_by_author()`                                    | `bitbucket pr by-author`                   | 0.3.0   | done   |
| `client.user.emails()`, `email()`                                 | `bitbucket user email list`, `get`         | 0.8.0   | done   |
| `client.users(id).get()`                                          | `bitbucket user get`                       | 0.8.0   | done   |
| `client.users(id).ssh_keys` CRUD, `gpg_keys`                      | `bitbucket user ssh-key`, `gpg-key`        | 0.8.0   | done   |
| `client.users(id).pipelines_config.variables`, `client.teams(id)` | `bitbucket user variable`, `team variable` | 0.8.0   | done   |
| `ws.search.code()`                                                | `bitbucket search code`                    | 0.8.0   | done   |

## Repositories and projects

| SDK                                                                          | CLI command                                                                                         | Release | Status |
| ---------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------- | ------- | ------ |
| `ws.repositories.list()`, `get()`                                            | `bitbucket repo list`, `get`                                                                        | 0.1.0   | done   |
| `ws.repositories.create()`, `update()`, `delete()`                           | `bitbucket repo create`, `update`, `delete`                                                         | 0.2.0   | done   |
| `ws.repositories.create_fork()`, `forks()`, `watchers()`                     | `bitbucket repo fork`, `forks`, `watchers`                                                          | 0.2.0   | done   |
| `ws.repositories.hooks()` CRUD, `client.hook_events`                         | `bitbucket webhook`, `hook-event types`, `list`                                                     | 0.2.0   | done   |
| `ws.repositories.commit_pull_requests()`, `pull_request_activity()`          | `bitbucket commit prs`, `pr activity`                                                               | 0.3.0   | done   |
| `ws.projects` CRUD                                                           | `bitbucket project`                                                                                 | 0.2.0   | done   |
| `project.default_reviewers`, `branching_model`, `permissions`, `deploy_keys` | `bitbucket default-reviewer`, `branching-model`, `permission-config`, `deploy-key` with `--project` | 0.5.0   | done   |

## Pull requests

| SDK                                                                       | CLI command                                    | Release | Status |
| ------------------------------------------------------------------------- | ---------------------------------------------- | ------- | ------ |
| `repo.pull_requests` create, get, list, update                            | `bitbucket pr create`, `get`, `list`, `update` | 0.3.0   | done   |
| `approve`, `unapprove`, `request_changes`, `unrequest_changes`, `decline` | `bitbucket pr approve`, `decline`, ...         | 0.3.0   | done   |
| `merge`, `merge_task_status`, `merge_and_wait`, `mergeability_checks`     | `bitbucket pr merge`, `checks`                 | 0.3.0   | done   |
| `diff`, `patch`, `diffstat`, `commits`, `conflicts`, `activity`           | `bitbucket pr diff`, `patch`, `files`, ...     | 0.3.0   | done   |
| `comments(id)` CRUD, `resolve`, `unresolve`                               | `bitbucket pr comment`                         | 0.3.0   | done   |
| `tasks(id)` CRUD, `statuses(id)`, `properties(id)`                        | `bitbucket pr task`, `status`, `property`      | 0.3.0   | done   |

## Refs, commits and source

| SDK                                                                      | CLI command                                                                                            | Release | Status |
| ------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------ | ------- | ------ |
| `repo.refs` list, `branches` and `tags` create, get, delete, list        | `bitbucket branch`, `tag`, `ref list`                                                                  | 0.4.0   | done   |
| `repo.commits` get, list, list_from, list_by_post, merge_base            | `bitbucket commit get`, `list`                                                                         | 0.4.0   | done   |
| `repo.commits` approve, unapprove, diff, patch, diffstat, file_conflicts | `bitbucket commit approve`, `diff`, ...                                                                | 0.4.0   | done   |
| `repo.commits.comments(commit)` CRUD, `properties(commit)`               | `bitbucket commit comment`, `property`                                                                 | 0.4.0   | done   |
| `repo.source` create_commit, list, list_path, read, file_history         | `bitbucket source ls`, `cat`, `history`, `commit`                                                      | 0.4.0   | done   |
| `repo.commit_statuses` list, create, get, update                         | `bitbucket commit status`                                                                              | 0.4.0   | done   |
| `repo.commits.reports(commit)` and `annotations`                         | `bitbucket report list`, `get`, `put`, `delete`; `annotation list`, `get`, `put`, `put-many`, `delete` | 0.4.0   | done   |
| `repo.downloads` list, get, upload, delete                               | `bitbucket download`                                                                                   | 0.4.0   | done   |

## Repository settings

| SDK                                                              | CLI command                    | Release | Status |
| ---------------------------------------------------------------- | ------------------------------ | ------- | ------ |
| `repo.branch_restrictions` CRUD                                  | `bitbucket branch-restriction` | 0.5.0   | done   |
| `repo.branching_model` get, settings, update_settings, effective | `bitbucket branching-model`    | 0.5.0   | done   |
| `repo.default_reviewers` list, get, add, remove, effective       | `bitbucket default-reviewer`   | 0.5.0   | done   |
| `repo.deploy_keys` CRUD                                          | `bitbucket deploy-key`         | 0.5.0   | done   |
| `repo.permissions` groups, users, override settings              | `bitbucket permission-config`  | 0.5.0   | done   |
| `repo.properties` get, put, delete                               | `bitbucket repo property`      | 0.5.0   | done   |

## Pipelines, environments and deployments

| SDK                                                                          | CLI command                                                                                           | Release | Status |
| ---------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------- | ------- | ------ |
| `repo.pipelines` create, get, list, stop, steps, step                        | `bitbucket pipeline run`, `get`, `list`, `stop`, `steps`, `step`                                      | 0.6.0   | done   |
| `repo.pipelines` step_log, container_log, test_reports, test_cases           | `bitbucket pipeline log`, `tests`, `test-cases`, `test-case-reasons`                                  | 0.6.0   | done   |
| `repo.pipelines_config` get, update, update_build_number                     | `bitbucket pipeline config`                                                                           | 0.6.0   | done   |
| `variables`, `schedules`, `known_hosts`, `ssh_key_pair`, `caches`, `runners` | `bitbucket pipeline variable`, `schedule`, `known-host`, `ssh-key`, `cache`, `runner`                 | 0.6.0   | done   |
| `ws.pipelines_config` variables, runners, OIDC configuration and keys        | `bitbucket pipeline variable`, `runner` without `--repo`; `workspace oidc-configuration`, `oidc-keys` | 0.6.0   | done   |
| `repo.environments` CRUD, `variables(env)`                                   | `bitbucket environment`, `environment variable`                                                       | 0.7.0   | done   |
| `repo.deployments` get, list                                                 | `bitbucket deployment`                                                                                | 0.7.0   | done   |

## Snippets

| SDK                                                                       | CLI command                                                                 | Release | Status |
| ------------------------------------------------------------------------- | --------------------------------------------------------------------------- | ------- | ------ |
| `ws.snippets` create, get, list, update, delete; `client.snippets.create` | `bitbucket snippet`                                                         | 0.9.0   | done   |
| `snippet.comments` CRUD, `commits`, `diff`, `patch`, `file`, `revision`   | `bitbucket snippet comment`, `commits`, `diff`, `patch`, `file`, `revision` | 0.9.0   | done   |
| `snippet.watch`, `unwatch`, `is_watching`, `watchers`                     | `bitbucket snippet watch`, `unwatch`, `is-watching`, `watchers`             | 0.9.0   | done   |

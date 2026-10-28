---
type: reference
title: Claude Code install scopes
description: user, project, and local scopes — which settings file each writes to, the precedence order, and when each is the right choice.
tags: [agents, claude-code]
status: stable
stale_after: 2027-03-29T00:00:00Z
sources:
  - id: claude-discover-plugins
    resource: https://code.claude.com/docs/en/discover-plugins
    title: Discover and install Claude Code plugins
    author: team:anthropic
  - id: claude-loading
    resource: https://code.claude.com/docs/en/plugins/loading
    title: How Claude Code loads plugins
    author: team:anthropic
---

# Claude Code install scopes

Every install, by `/plugin install` or `claude plugin install`, is
recorded in a settings file under one of three scopes.[^claude-discover-plugins]

| Scope     | Settings file                        | Reaches                                 |
| :-------- | :----------------------------------- | :-------------------------------------- |
| `user`    | `~/.claude/settings.json`            | You, in every project on this machine   |
| `project` | `.claude/settings.json` (committed)  | Everyone who works in the repository    |
| `local`   | `.claude/settings.local.json`        | You, in this repository only            |

The entry is written under `enabledPlugins` in that file.

## Which scope to pick

* **`user`**: the default for `claude plugin install`. Use it for
  plugins you want in every project.
* **`project`**: the entry lives in the committed `.claude/settings.json`.
  Use it when the repository itself depends on the plugin. Committing the
  entry enables the plugin for collaborators but does not download it, so
  each collaborator runs
  `claude plugin install <plugin>@<marketplace> --scope project` once.[^claude-loading]
* **`local`**: the entry lives in `.claude/settings.local.json`. Use it
  for a personal setup in one repository.

## Precedence

When the same plugin is set at several scopes, `local` overrides
`project`, and `project` overrides `user`.[^claude-loading]

[^claude-discover-plugins]: Discover and install Claude Code plugins
[^claude-loading]: How Claude Code loads plugins

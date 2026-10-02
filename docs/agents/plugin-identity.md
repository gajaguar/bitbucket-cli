---
type: reference
title: Plugin identity
description: The marketplace, plugin, and skill names for this project, plus the prerequisites and copy-ready install commands.
resource: https://github.com/gajaguar/bitbucket-cli
tags: [agents]
status: stable
sources:
  - id: claude-discover-plugins
    resource: https://code.claude.com/docs/en/discover-plugins
    title: Discover and install Claude Code plugins
    author: team:anthropic
---

# Plugin identity

This project ships as a Claude Code plugin and an Agent Skills
directory.[^claude-discover-plugins] It does not ship an MCP server.
The marketplace, plugin, and skill names below match this repository's
own `.claude-plugin/` and `skills/` directories.

## Names

| Asset       | Name                     |
| :---------- | :----------------------- |
| Repository  | `gajaguar/bitbucket-cli` |
| Marketplace | `bitbucket-cli-skills`   |
| Plugin      | `bitbucket-cli`          |

## Skills

| Skill                     | Trigger phrasing                                                                                                         |
| :------------------------ | :----------------------------------------------------------------------------------------------------------------------- |
| `bitbucket-pull-requests` | "open a PR", "review PR 12", "comment on the PR", "approve", "merge the PR", "is the PR mergeable"                       |
| `bitbucket-pipelines`     | "run the pipeline", "why did the build fail", "show the build log", "add a pipeline variable", environments, deployments |
| `bitbucket-cli`           | "bitbucket login", "switch workspace", "list repos", "create a branch", "add a webhook", "protect a branch", snippets    |

Each skill carries its own copy of `references/exit-codes.md`, so it works
when read alone.

## Prerequisites

- Install the `bitbucket-unofficial-cli` Python package
  (`pipx install bitbucket-unofficial-cli` or
  `uv tool install bitbucket-unofficial-cli`).
- Run `bitbucket auth login` before the skills will work. They delegate to
  the credential the CLI stores; an agent never sees it.

## Install

Claude Code:

```text
/plugin marketplace add gajaguar/bitbucket-cli
/plugin install bitbucket-cli@bitbucket-cli-skills
/reload-plugins
```

Any other Agent Skills-compatible agent:

```bash
npx skills add gajaguar/bitbucket-cli
```

opencode:

```bash
npx skills add gajaguar/bitbucket-cli -a opencode -y
```

See [`install-channels.md`](install-channels.md) for what each channel
delivers, and the rest of `docs/agents/` for scopes, management, and
opencode's skill discovery.

[^claude-discover-plugins]: Discover and install Claude Code plugins

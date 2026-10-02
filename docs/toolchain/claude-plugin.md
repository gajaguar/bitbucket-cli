---
type: tool
title: The Claude Code plugin
description: The repository root is a Claude Code plugin whose three skills teach an agent to drive the bitbucket CLI.
tags: [agents]
status: stable
---

# The Claude Code plugin

`.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json` make the
repository root installable with `/plugin marketplace add
gajaguar/bitbucket-cli`. It ships three Agent Skills under `skills/`:
`bitbucket-pull-requests`, `bitbucket-pipelines` and `bitbucket-cli`. Each
carries its own copy of `references/exit-codes.md` so it works when read alone.

`make skills-validate`, part of `make check`, validates every
`skills/*/SKILL.md` against the Agent Skills spec. A unit test fails when
`plugin.json`'s `version` differs from `project.version`, so a release bumps
both. The plugin has no MCP server.

See [`docs/agents/`](../agents/index.md) for install channels, scopes, and management.

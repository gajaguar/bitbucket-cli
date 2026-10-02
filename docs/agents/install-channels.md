---
type: guideline
title: Install channels
description: Three ways to install agent skills today (the Claude Code marketplace, the npx skills CLI, and opencode's native skill tool) and what each delivers.
tags: [agents, install]
status: stable
stale_after: 2027-03-29T00:00:00Z
sources:
  - id: claude-discover-plugins
    resource: https://code.claude.com/docs/en/discover-plugins
    title: Discover and install Claude Code plugins
    author: team:anthropic
  - id: vercel-skills
    resource: https://github.com/vercel-labs/skills
    title: vercel-labs/skills (the `npx skills` CLI)
    author: team:vercel-labs
  - id: opencode-skills
    resource: https://opencode.ai/docs/skills/
    title: opencode Skills
    author: team:sst-opencode
---

# Install channels

A project that ships agent assets can be installed three ways. Pick
the channel that matches the user's agent.

| Channel             | Installs                | Auto-update |
| :------------------ | :---------------------- | :---------- |
| Claude Code plugin  | Skills (and any hooks)  | Opt-in      |
| `npx skills`        | Skills only             | No          |
| opencode skill tool | Skills only             | No          |

For a Claude Code plugin, auto-update is off by default for third-party
marketplaces and on for the official Anthropic marketplaces. For
`npx skills`, run `npx skills update` by hand.

## Claude Code plugin

A Claude Code plugin is the richest channel: a marketplace install
pulls the skills and runs any plugin hooks. Auto-update is off by default
for third-party marketplaces; turn it on per marketplace or update by hand, as
described in
[`claude-code-plugin-updates.md`](claude-code-plugin-updates.md).[^claude-discover-plugins]

## `npx skills`

The `npx skills` CLI ([vercel-labs/skills](https://github.com/vercel-labs/skills))
installs a repository's skills into the right per-agent path,
symlinked by default. It supports multiple agents in one command (`-a
claude-code -a opencode`), a global install (`-g`), and independent
copies instead of symlinks (`--copy`); see
[`npx-skills-install.md`](npx-skills-install.md).[^vercel-skills]

## opencode

opencode does not have a plugin marketplace. It reads skills from a
small, fixed set of paths and exposes them through the `skill` tool;
see [`opencode-skill-discovery.md`](opencode-skill-discovery.md).[^opencode-skills]

[^claude-discover-plugins]: Discover and install Claude Code plugins
[^vercel-skills]: vercel-labs/skills (the `npx skills` CLI)
[^opencode-skills]: opencode Skills

---
type: playbook
title: Installing through the Claude Code marketplace
description: Add a marketplace and install a plugin from it inside a Claude Code session, including the one-step form and the reload.
tags: [agents, claude-code]
status: stable
stale_after: 2027-03-29
sources:
  - id: claude-discover-plugins
    resource: https://code.claude.com/docs/en/discover-plugins
    title: Discover and install Claude Code plugins
    author: team:anthropic
---

# Installing through the Claude Code marketplace

Use the `/plugin` slash commands inside a Claude Code session to add a
marketplace and install a plugin from it.[^claude-discover-plugins]

## Two commands

```text
/plugin marketplace add <owner>/<repo>[#ref]
/plugin install <plugin>@<marketplace>
```

Add `#ref` to pin a branch or tag. `<marketplace>` is the name the
marketplace registered under, and `<plugin>` is the plugin's name. Both
names are listed in [`plugin-identity.md`](plugin-identity.md).

In a session, `/plugin install` does not install right away. It opens
the `/plugin` panel on the plugin's details so you can review it and
pick a scope: user, project (all collaborators on the repository), or
local (you, this repository only).

## One-step form

To add a marketplace and install from it in one command, pass
`--marketplace` with the marketplace source. This form requires Claude
Code v2.1.275 or later.

```text
/plugin install <plugin> --marketplace <owner>/<repo>
```

Give the plugin name by itself, without an `@<marketplace>` suffix. If
the marketplace is not added yet, Claude Code shows the source it
resolved and asks you to confirm before adding it.

## Scope

You choose the scope in the panel, not with a flag. The `--scope` flag
belongs to the shell command; see
[`claude-code-shell-install.md`](claude-code-shell-install.md). For what
each scope writes, see
[`claude-code-install-scopes.md`](claude-code-install-scopes.md).

## Reload

The install summary ends with one of two outcomes: `Plugin is now
active.`, or `Run /reload-plugins to activate.` In the second case, the
panel closes and Claude Code runs the reload for you. If the reload
would invalidate the prompt cache, Claude Code warns and leaves the
plugin pending; run `/reload-plugins --force` to activate it
anyway.[^claude-discover-plugins]

[^claude-discover-plugins]: Discover and install Claude Code plugins

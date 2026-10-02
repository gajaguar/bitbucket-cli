---
type: playbook
title: Installing from a script or CI
description: The claude plugin CLI installs and manages plugins from your shell, with user scope by default and a --yes flag for command-source prompts.
tags: [agents, claude-code, ci]
status: stable
stale_after: 2027-03-29T00:00:00Z
sources:
  - id: claude-discover-plugins
    resource: https://code.claude.com/docs/en/discover-plugins
    title: Discover and install Claude Code plugins
    author: team:anthropic
  - id: claude-cli-reference
    resource: https://code.claude.com/docs/en/plugins/cli-reference
    title: Claude Code plugin CLI reference
    author: team:anthropic
---

# Installing from a script or CI

Run `claude plugin` subcommands in your shell to install and manage
plugins without starting a Claude Code session, for example from a setup
script.[^claude-discover-plugins]

## Commands

```bash
claude plugin marketplace add <owner>/<repo>[#ref]
claude plugin install <plugin>@<marketplace>
claude plugin list
```

The marketplace must be added before you install from it.

## Scopes

`claude plugin install` installs at user scope by default. Pass
`--scope project` or `--scope local` to change it. `claude plugin
enable` and `claude plugin disable` act on the most specific scope whose
settings already list the plugin unless you pass `--scope`. See
[`claude-code-install-scopes.md`](claude-code-install-scopes.md) for what
each scope writes to.[^claude-cli-reference]

## The `--yes` flag

Some plugins install by running a command their marketplace names (a
`command` source). Claude Code shows the command and asks you to accept
it. A script has no one to answer, so pass `--yes` to accept that prompt.
`--yes` does not skip any other prompt.[^claude-cli-reference]

## When plugins load

Plugins you install from the shell load the next time you start Claude
Code, or when you run `/reload-plugins` in a session that is already
open.[^claude-discover-plugins]

[^claude-discover-plugins]: Discover and install Claude Code plugins
[^claude-cli-reference]: Claude Code plugin CLI reference

---
type: playbook
title: Updating and uninstalling Claude Code plugins
description: Auto-update is off by default for third-party marketplaces, so update by hand and reload; uninstall the plugin and remove the marketplace when you are done.
tags: [agents, claude-code]
status: stable
stale_after: 2027-03-29
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

# Updating and uninstalling Claude Code plugins

Auto-update is off by default for third-party marketplaces, so update
those plugins by hand. It is on by default for the official Anthropic
marketplaces and for marketplaces added from claude.ai.[^claude-discover-plugins]

## Update by hand

In a Claude Code session, refresh the marketplace, then update the
plugin from the `/plugin` panel:

```text
/plugin marketplace update <marketplace>
```

Open the plugin on the **Installed** tab in `/plugin` and select
**Update now**.

From your shell:

```bash
claude plugin marketplace update <marketplace>
claude plugin update <plugin>@<marketplace>
```

The running session keeps the versions it already loaded. Run
`/reload-plugins` to apply an update in that session, or start a new
session.[^claude-loading]

## Turn auto-update on for a marketplace

Run `/plugin`, open the **Marketplaces** tab, select the marketplace,
and choose **Enable auto-update**.[^claude-discover-plugins]

## Disable without uninstalling

Use `/plugin disable <plugin>` in a session, or `claude plugin disable
<plugin>@<marketplace>` in your shell, to keep the plugin installed but
stop loading it.

## Uninstall

```text
/plugin uninstall <plugin>@<marketplace>
/plugin marketplace remove <marketplace>
```

Uninstalling a plugin leaves the marketplace registered. Removing a
marketplace uninstalls every plugin you installed from it and removes
their `enabledPlugins` entries from your settings files.[^claude-discover-plugins]

[^claude-discover-plugins]: Discover and install Claude Code plugins
[^claude-loading]: How Claude Code loads plugins

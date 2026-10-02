---
type: reference
title: Invoking a Claude Code skill
description: The /<plugin>:<skill> slash form, automatic triggering by description, and three ways to verify a plugin skill is installed.
tags: [agents, claude-code, skills]
status: stable
stale_after: 2027-03-29
sources:
  - id: claude-skills
    resource: https://code.claude.com/docs/en/skills
    title: Claude Code skills
    author: team:anthropic
  - id: claude-discover-plugins
    resource: https://code.claude.com/docs/en/discover-plugins
    title: Discover and install Claude Code plugins
    author: team:anthropic
---

# Invoking a Claude Code skill

A skill from an installed plugin is invoked two ways.[^claude-skills][^claude-discover-plugins]

## Explicit invocation

Plugin skills are namespaced as `/<plugin>:<skill>`:

```text
/<plugin>:<skill>
```

`<skill>` is the skill's directory name under the plugin's `skills/`
folder, or the `name` in its frontmatter when one is set. `<plugin>` is
the plugin's name. Both are listed in
[`plugin-identity.md`](plugin-identity.md).[^claude-skills]

## Automatic triggering

Claude uses each skill's `description` to decide when to load the skill
automatically, so put the use case and the user phrasing that should
trigger the skill in `description`.[^claude-skills]

## Verifying the install

Any one of these confirms the plugin is installed:[^claude-discover-plugins]

* Type `/` in a session and look for the plugin's skills as `/<plugin>:<skill>`.
* Open the **Installed** tab in `/plugin`, which lists each plugin with its scope.
* Run `claude plugin list` in your shell, which prints `Version`,
  `Scope`, and `Status` for each plugin.

[^claude-skills]: Claude Code skills
[^claude-discover-plugins]: Discover and install Claude Code plugins

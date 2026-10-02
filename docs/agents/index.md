# Agents

Install this project's skills in Claude Code, in `npx skills`, or in
opencode, and learn what each channel delivers.

## This project

* [Plugin identity](plugin-identity.md) - the marketplace, plugin, and
  skill names for this project, plus copy-ready install commands.

## Shared notes

* [Agent Skills format](agent-skills-format.md) - `SKILL.md`, its
  required and recommended fields, progressive disclosure, and the
  `references/` subdirectory.
* [Install channels](install-channels.md) - three ways to install an
  agent plugin today, and what each delivers.

### Claude Code

* [Installing through the marketplace](claude-code-marketplace-install.md) -
  the in-session `/plugin` flow.
* [Installing from a script or CI](claude-code-shell-install.md) - the
  `claude plugin` CLI and a CI recipe.
* [Install scopes](claude-code-install-scopes.md) - `user`, `project`,
  and `local`: which settings file each writes to, and which wins on
  conflict.
* [Invoking a skill](claude-code-skill-invocation.md) - the
  `/<plugin>:<skill>` slash form and automatic triggering by
  `description`.
* [Updating and uninstalling](claude-code-plugin-updates.md) - update
  by hand, disable without uninstall, and the marketplace remove step.

### `npx skills`

* [Installing skills with `npx skills`](npx-skills-install.md) - the
  install command, its flags, and the per-agent paths.
* [Managing installed skills](npx-skills-manage.md) - list, update,
  and remove.

### opencode

* [opencode skill discovery](opencode-skill-discovery.md) - the paths
  opencode scans, the worktree walk-up rule, and name validation.
* [opencode skill permissions](opencode-skill-permissions.md) -
  `permission.skill` and the per-agent `skill: false` switch.
* [opencode MCP configuration](opencode-mcp-config.md) - the `mcp` key,
  config path precedence, and `opencode mcp list`.

See [`log.md`](../log.md) for the bundle's change history.

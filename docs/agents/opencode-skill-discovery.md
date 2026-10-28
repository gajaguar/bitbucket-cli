---
type: reference
title: opencode skill discovery
description: The project and global paths opencode reads skills from, the walk-up to the git worktree, and the name and description rules.
tags: [agents, opencode]
status: stable
stale_after: 2027-03-29T00:00:00Z
sources:
  - id: opencode-skills
    resource: https://opencode.ai/docs/skills/
    title: opencode Skills
    author: team:sst-opencode
---

# opencode skill discovery

opencode discovers skills from a fixed set of paths and exposes them
through the `skill` tool.[^opencode-skills]

## Project paths

Each skill is a folder containing a `SKILL.md`:

* `.opencode/skills/<skill>/SKILL.md`
* `.claude/skills/<skill>/SKILL.md`
* `.agents/skills/<skill>/SKILL.md`

## Worktree walk-up

opencode walks up from the current working directory until it reaches
the git worktree, loading matching skill files along the way. A skill
in the worktree's top-level `.opencode/skills/` is therefore visible from
any subdirectory of the same worktree.

## Global paths

opencode also loads global definitions:

* `~/.config/opencode/skills/<skill>/SKILL.md`
* `~/.claude/skills/<skill>/SKILL.md`
* `~/.agents/skills/<skill>/SKILL.md`

## Frontmatter and name validation

`name` and `description` are required; `license`, `compatibility`, and
`metadata` are optional. The `name` must be 1-64 characters, match
`^[a-z0-9]+(-[a-z0-9]+)*$`, and match the containing directory name. The
`description` must be 1-1024 characters.

[^opencode-skills]: opencode Skills

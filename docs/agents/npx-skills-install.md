---
type: playbook
title: Installing skills with `npx skills`
description: npx skills add installs a repository's skills into one or more agent paths, symlinked by default, with flags for agent, scope, skill selection, and list-only.
tags: [agents, npx-skills]
status: stable
stale_after: 2027-03-29
sources:
  - id: vercel-skills
    resource: https://github.com/vercel-labs/skills
    title: vercel-labs/skills (the `npx skills` CLI)
    author: team:vercel-labs
  - id: skills-sh
    resource: https://skills.sh
    title: skills.sh
    author: team:vercel-labs
---

# Installing skills with `npx skills`

`npx skills` ([vercel-labs/skills](https://github.com/vercel-labs/skills))
installs a repository's skills into the path each agent expects, with no
plugin hooks or MCP. By default it symlinks each agent to one canonical
copy; pass `--copy` for independent copies. It is the right channel when
the agent is not Claude Code or the project does not need
auto-update.[^vercel-skills]

## Install for several agents at once

```bash
npx skills add <owner>/<repo> -a claude-code -a opencode -y
```

`-a` names an agent (for example `claude-code` or `opencode`); use
`-a '*'` for every agent. `-y` skips the confirmation prompts.

## Flags

| Flag                 | Effect                                                                 |
| :------------------- | :--------------------------------------------------------------------- |
| `-a, --agent`        | Agents to install to; `'*'` for all agents                             |
| `-s, --skill`        | Skill names to install; `'*'` for all skills                           |
| `-g, --global`       | Install at user level instead of project level                         |
| `-l, --list`         | List the skills in the repository without installing                   |
| `-y, --yes`          | Skip confirmation prompts                                              |
| `--copy`             | Copy files instead of symlinking to the agent directories              |
| `--all`              | Shorthand for `--skill '*' --agent '*' -y`                             |
| `--json`             | Machine-readable output with no ANSI codes                             |
| `--full-depth`       | Search all subdirectories even when a root `SKILL.md` exists           |

## Where `npx skills` writes

Project scope is the default; `-g` writes to the user-level path. The
paths for the two agents this documentation covers:[^vercel-skills]

| Agent         | Project path       | Global path                  |
| :------------ | :----------------- | :--------------------------- |
| `claude-code` | `.claude/skills/`  | `~/.claude/skills/`          |
| `opencode`    | `.agents/skills/`  | `~/.config/opencode/skills/` |

Run `npx skills add <owner>/<repo> --list` first to see which skills the
repository offers without installing anything.[^skills-sh]

[^vercel-skills]: vercel-labs/skills (the `npx skills` CLI)
[^skills-sh]: skills.sh

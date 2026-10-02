---
type: reference
title: Agent Skills format
description: SKILL.md frontmatter fields and their constraints, progressive disclosure, and the optional references/ subdirectory.
tags: [agents, skills]
status: stable
stale_after: 2027-03-29T00:00:00Z
sources:
  - id: agentskills-spec
    resource: https://agentskills.io/specification
    title: Agent Skills specification
    author: team:agentskills
---

# Agent Skills format

An Agent Skill is a directory that contains a `SKILL.md` file: YAML
frontmatter followed by Markdown instructions. Agents load the `name`
and `description` at startup to decide when a skill applies.[^agentskills-spec]

| Field           | Required | Purpose                                     |
| :-------------- | :------- | :------------------------------------------ |
| `name`          | Yes      | Skill identifier                            |
| `description`   | Yes      | What the skill does and when to use it      |
| `license`       | No       | License name or bundled license file        |
| `compatibility` | No       | Environment requirements                    |
| `metadata`      | No       | String-to-string map of extra properties    |
| `allowed-tools` | No       | Pre-approved tools (experimental)           |

Constraints from the specification:[^agentskills-spec]

* `name`: 1-64 characters; lowercase letters, digits, and hyphens only;
  no leading, trailing, or consecutive hyphens; must match the parent
  directory name.
* `description`: 1-1024 characters; say what the skill does and when to
  use it.
* `license`: a license name or a reference to a bundled license file;
  keep it short.
* `compatibility`: 1-500 characters; for example the intended product,
  system packages, or network access.
* `metadata`: a map from string keys to string values; use reasonably
  unique key names.
* `allowed-tools`: a space-separated string of pre-approved tools.
  Experimental, so support varies between agents.

## Progressive disclosure

Agents load a skill in three steps:[^agentskills-spec]

1. **Metadata** (about 100 tokens): `name` and `description`, loaded
   at startup for every skill.
2. **Instructions** (under 5000 tokens recommended): the full
   `SKILL.md` body, loaded when the skill activates.
3. **Resources**: files under `scripts/`, `references/`, or `assets/`,
   loaded only when needed.

Keep `SKILL.md` under 500 lines and move detailed material into
separate files.

## `references/` subdirectory

A skill may put additional documentation under `references/` (for
example `REFERENCE.md` or a domain-specific file) and link to it with a
relative path from the skill root. Agents read these files on demand, so
keep each one focused. Keep references one level deep from
`SKILL.md`.[^agentskills-spec]

[^agentskills-spec]: Agent Skills specification

---
type: playbook
title: Managing installed skills
description: npx skills list, update, and remove, plus find, use, and init, as shown by the CLI help.
tags: [agents, npx-skills]
status: stable
stale_after: 2027-03-29T00:00:00Z
sources:
  - id: vercel-skills
    resource: https://github.com/vercel-labs/skills
    title: vercel-labs/skills (the `npx skills` CLI)
    author: team:vercel-labs
---

# Managing installed skills

`npx skills` manages installed skills with the commands below; the
install command is covered in
[`npx-skills-install.md`](npx-skills-install.md).[^vercel-skills]

## List what is installed

```bash
npx skills list
```

`list` (alias `ls`) shows the installed skills.

## Update

```bash
npx skills update [skills...]
```

`update` (alias `upgrade`) updates skills to their latest versions. Pass
`-g` for global skills only, `-p` for project skills only, or `-y` to
skip the scope prompt (it picks project scope inside a project, global
otherwise).

## Remove

```bash
npx skills remove [skills...]
```

`remove` (alias `rm`) removes installed skills; with no names it opens an
interactive selection. Pass `-g` for global scope, `-a` for specific
agents, `-s` for skill names (`'*'` for all), `-y` to skip
confirmation, or `--all` to remove every installed skill.

## Other commands

* `find [query]` searches for skills interactively.
* `use <package>@<skill>` generates a prompt for using one skill
  without installing it.
* `init [name]` creates a `SKILL.md` for a new skill.

[^vercel-skills]: vercel-labs/skills (the `npx skills` CLI)

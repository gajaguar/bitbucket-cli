---
type: reference
title: opencode skill permissions
description: permission.skill maps name patterns to allow, deny, or ask, and tools.skill false disables skills per agent.
tags: [agents, opencode]
status: stable
stale_after: 2027-03-29
sources:
  - id: opencode-skills
    resource: https://opencode.ai/docs/skills/
    title: opencode Skills
    author: team:sst-opencode
---

# opencode skill permissions

Two configuration knobs gate which skills opencode loads. Both live in
opencode's own config file.[^opencode-skills]

## `permission.skill`

The `permission.skill` key is an object that maps a skill name or
wildcard pattern to `"allow"`, `"deny"`, or `"ask"`:

```json
{
  "permission": {
    "skill": {
      "*": "allow",
      "internal-*": "deny",
      "<skill>": "ask"
    }
  }
}
```

* `"allow"` loads the skill immediately.
* `"deny"` hides the skill from the agent.
* `"ask"` prompts the user before loading.

## Per-agent `skill: false`

Set `tools: { skill: false }` on an agent to disable the `skill` tool
for that agent. For a custom agent, put it in the agent's frontmatter;
for a built-in agent, put it in the agent's entry in `opencode.json`.
Use this when an agent should never load a skill.

[^opencode-skills]: opencode Skills

---
type: reference
title: opencode MCP configuration
description: The mcp key for local and remote servers, the config file precedence list, and the opencode mcp commands.
tags: [agents, opencode, mcp]
status: stable
stale_after: 2027-03-29
sources:
  - id: opencode-mcp
    resource: https://opencode.ai/docs/mcp-servers/
    title: opencode MCP servers
    author: team:sst-opencode
  - id: opencode-config
    resource: https://opencode.ai/docs/config/
    title: opencode config
    author: team:sst-opencode
---

# opencode MCP configuration

opencode reads MCP server definitions from its config under an `mcp`
key.[^opencode-mcp]

## Local server

```json
{
  "mcp": {
    "<name>": {
      "type": "local",
      "command": ["<executable>", "<arg>", "..."],
      "enabled": true,
      "environment": { "<KEY>": "<value>" }
    }
  }
}
```

| Key           | Purpose                                                              |
| :------------ | :------------------------------------------------------------------- |
| `type`        | `"local"` for a process the CLI starts, or `"remote"` for a URL      |
| `command`     | Argument array for a local server: executable first, then arguments  |
| `enabled`     | Enable or disable the server                                         |
| `environment` | Environment variables for a local server's process                   |
| `cwd`         | Working directory for a local server                                 |
| `timeout`     | Milliseconds to wait when fetching tools (default 5000)              |

## Remote server

A remote server uses `"type": "remote"` with a `url`, and optionally
`headers` and `oauth`, in place of `command`.[^opencode-mcp]

## Config file precedence

opencode merges config sources; later sources override earlier ones
only for conflicting keys. The order is:[^opencode-config]

1. Remote config (from `.well-known/opencode`)
2. Global config (`~/.config/opencode/opencode.json`)
3. Custom config (the `OPENCODE_CONFIG` environment variable)
4. Project config (`opencode.json` in the project root)
5. `.opencode` directories
6. Inline config (the `OPENCODE_CONFIG_CONTENT` environment variable)
7. Managed config files
8. macOS managed preferences

Put a server for one project in the project's `opencode.json`; put a
server shared across projects in the global config.

## CLI commands

```bash
opencode mcp list
```

`opencode mcp list` shows every MCP server and its authentication
status. Related commands are `opencode mcp auth <server-name>` (start
the OAuth flow), `opencode mcp logout <server-name>` (remove stored
credentials), and `opencode mcp debug <server-name>` (diagnose
connection and OAuth problems).[^opencode-mcp]

[^opencode-mcp]: opencode MCP servers
[^opencode-config]: opencode config

---
type: rule
title: Layering
description: Layers point downward only, and Bitbucket is reached through the SDK except for the OAuth token exchange.
tags: [architecture]
status: stable
---

# Layering

```text
main
 └─ commands ──► services ──► runtime ──► auth ─┐
        │                       │               ├──► bitbucket-unofficial-sdk
        └──► output             └──► config ────┘
```

| Layer      | Holds                                                               |
| ---------- | ------------------------------------------------------------------- |
| `main`     | The Typer app, the global options and the wiring of `Services`      |
| `commands` | One module per noun (`auth`, `config`, `user`, `workspace`, `repo`) |
| `services` | Logic shared by commands that is not about one noun, such as paging |
| `runtime`  | `AppContext`, error handling, exit codes, the SDK client factory    |
| `auth`     | Credential kinds, the stores they live in, and the OAuth flows      |
| `config`   | Profiles, the settings file and how global options are resolved     |
| `output`   | The renderers and the column definitions of each resource           |

A layer imports only from the layers below it. Nothing imports from
`commands`.

## Commands stay thin

A command parses its options, asks `AppContext` for a client, calls one SDK
method and hands the result to `AppContext.render`. The SDK client is created
on first use, so a command that never calls Bitbucket, such as `config list`,
needs no credential.

## The SDK is the only way in

Commands never build a request. When the SDK lacks a capability, it is added
to the SDK first and the CLI raises its SDK floor in `pyproject.toml`.

One module breaks the rule on purpose. `auth/oauth.py` calls Bitbucket's
OAuth authorize and token endpoints with `httpx`, because the SDK takes a
ready token and leaves obtaining and renewing it to the application. See
[Why the SDK does not acquire credentials](https://github.com/gajaguar/bitbucket-sdk/blob/main/docs/sdk/credential-sources.md).

## Everything injectable lives in `Services`

`Services` bundles the settings store, the credential stores, the SDK client
factory, the OAuth client and the function that opens a browser. The app is
built with `create_app(services_factory)`, so a test swaps any of them. The
tests run a real SDK client against a fake host with `respx` instead of
mocking SDK methods.

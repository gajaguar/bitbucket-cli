---
type: playbook
title: Setting up an OAuth consumer
description: How to create a Bitbucket OAuth consumer and log in with the authorization code or client credentials grant.
tags: [auth, oauth]
status: stable
---

# Setting up an OAuth consumer

An OAuth consumer lets the CLI act with a token that expires and renews
itself, instead of a long-lived API token.

## Create the consumer

In Bitbucket, open **Workspace settings → OAuth consumers → Add consumer**.

1. Give it a name.
2. Set the **Callback URL** to `http://127.0.0.1:8976/callback`. Bitbucket
   sends the browser back to the URL saved on the consumer, so it must match
   the port the CLI listens on. Another port needs `--callback-port` and a
   matching URL.
3. Tick the permissions the commands you plan to run need.
4. For the client credentials grant, tick **This is a private consumer**.
5. Save, then copy the **Key** and the **Secret**.

## Authorization code

The grant acts as you and needs a browser.

```bash
bitbucket auth login --oauth --client-id KEY
```

The CLI prompts for the secret, listens on `127.0.0.1` for the redirect, opens
the authorization page, checks the `state` it gets back, and exchanges the
code for tokens. It stores them with the consumer's key and secret so it can
renew the token without asking again.

On a machine without a browser, add `--no-browser`: the CLI prints the URL,
and you paste back the address your browser was redirected to.

## Client credentials

The grant acts as the consumer's owner and needs no browser, which suits
automation.

```bash
bitbucket auth login --oauth --client-credentials --client-id KEY
```

The grant has no refresh token, so the CLI requests a new token with the
stored key and secret when the old one expires.

## Renewing

Any command renews an expired token on its own. `bitbucket auth refresh`
renews it now, and `bitbucket auth status` shows when it expires.

If a renewal is rejected, for example because the consumer was deleted, the
command fails with exit code 4 and asks you to log in again.

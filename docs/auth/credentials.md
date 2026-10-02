---
type: reference
title: Credentials
description: The three credential kinds, where each one is read from and stored, and which HTTP header the SDK sends for it.
tags: [auth]
status: stable
---

# Credentials

## Kinds

| Kind           | Holds                                                                      | Header the SDK sends    | Renewed           |
| -------------- | -------------------------------------------------------------------------- | ----------------------- | ----------------- |
| `api_token`    | The account email and an Atlassian API token                               | `Authorization: Basic`  | Never             |
| `access_token` | A repository, project or workspace access token                            | `Authorization: Bearer` | Never             |
| `oauth`        | A consumer key and secret, an access token, a refresh token and its expiry | `Authorization: Bearer` | Before it expires |

An access token is scoped to the repository, project or workspace that issued
it and cannot read `/user`, so `auth login --access-token` checks it against
the selected workspace instead, and skips the check when none is selected.

## Where one is read from

The first source that has a credential for the profile wins.

1. **The environment.** `ATLASSIAN_USER_EMAIL` with `ATLASSIAN_API_TOKEN`, or
   `BITBUCKET_ACCESS_TOKEN`. It ignores the profile. Setting both kinds is a
   configuration error, as it is in the SDK.
2. **The system keyring.** Service `bitbucket-cli`, one entry per profile.
3. **A file.** `credentials.toml` in the config directory, mode `0600`, only
   when `auth login --insecure-storage` wrote it.

`auth login` writes to the keyring, or to the file with `--insecure-storage`,
and removes the profile's entry from the other.

## How it reaches the SDK

`runtime/client_factory.py` turns the credential into a `BitbucketClient`:
`email` and `api_token` for the first kind, `access_token` for the second.
For OAuth it passes a provider, `OAuthTokenProvider`, which the SDK calls on
every request. The provider returns the stored token until a minute before
its expiry, then renews it and hands the new credential back, and the context
writes it to the store it came from.

## Secrets stay out of reach

- No command takes a secret as an argument; they come from a hidden prompt,
  standard input or an environment variable.
- `auth status` and `auth login` print the secret masked to its last four
  characters. Only `auth token` prints a whole one.

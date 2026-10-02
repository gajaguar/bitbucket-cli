---
type: playbook
title: Releasing the CLI
description: How a change bumps the version, which bumps get a tag, and how a release reaches PyPI as bitbucket-unofficial-cli.
tags: [release]
status: stable
---

# Releasing the CLI

The rules for bumping, tagging and publishing are in
[Versioning, tags and releases](../conventions/versioning.md). This note adds
what is particular to this project.

## Names

The repository is `bitbucket-cli` and the PyPI distribution is
`bitbucket-unofficial-cli`. The command and the import package differ again:
`bitbucket` and `bitbucket_unofficial_cli`. The PyPI trusted publisher is
registered against the distribution name; see
[PyPI releases use Trusted Publishing](pypi-trusted-publishing.md).

## Steps

1. Set `project.version` in `pyproject.toml`, in the change's own
   `chore(release)` commit. `bitbucket --version` reads it from the installed
   metadata, so nothing else holds the version.
2. Merge the pull request.
3. For a minor or major bump, run `make release-tag` on the updated base
   branch. For a patch, run it when you decide to publish the patch.
4. Publish a GitHub Release from the tag when asked to; the workflow uploads
   to PyPI after the `pypi` environment's reviewer approves.

Before publishing, run `make build` and `uvx twine check dist/*`, and install
the wheel in a clean environment. PyPI never accepts the same version twice.

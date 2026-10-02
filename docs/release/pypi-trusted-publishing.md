---
type: decision
title: PyPI releases use Trusted Publishing
description: The publish workflow uploads to PyPI via OIDC trusted publishing triggered by a GitHub Release, not a long-lived API token.
tags: [release, ci]
status: stable
---

# PyPI releases use Trusted Publishing

Publishing a GitHub Release (`published` event) runs
[`.github/workflows/publish.yml`](../../.github/workflows/publish.yml): it
builds the sdist and wheel with `make build`, then uploads them with
[`pypa/gh-action-pypi-publish`](https://github.com/pypa/gh-action-pypi-publish)
under the `pypi` environment. The publish job authenticates with a
short-lived OIDC token instead of a stored `PYPI_API_TOKEN`, so no PyPI
secret exists anywhere in this repository.

## One-time PyPI-side setup

Before the first release, add this workflow as a trusted publisher on the
PyPI project
(`https://pypi.org/manage/project/bitbucket-cli/publishing/`, or the "pending
publisher" form under `https://pypi.org/manage/account/publishing/` if the
project does not exist on PyPI yet). The PyPI project name is the `name` in
`pyproject.toml`; if it ever differs from the repository name, register the
`pyproject.toml` one, or the first upload fails:

* Owner: `gajaguar`
* Repository name: `bitbucket-cli`
* Workflow name: `publish.yml`
* Environment name: `pypi`

Then, in the repository's settings, restrict the `pypi` environment to `v*`
tags and require a reviewer, so a release only uploads after an explicit
approval.

## Cutting a release

Releases are on demand; see
[`docs/conventions/versioning.md`](../conventions/versioning.md) for which
bumps get a tag.

1. Bump `project.version` in `pyproject.toml` only, as the versioning note
   describes, and merge the pull request.
2. Tag the merge commit with `make release-tag` if the bump is minor or major.
   For a patch, run it only when you decide to publish that patch.
3. Publish a GitHub Release from that `vX.Y.Z` tag; the build fails if the tag
   and `project.version` differ.
4. Approve the deployment in the `pypi` environment; the workflow uploads only
   after its reviewer approves.

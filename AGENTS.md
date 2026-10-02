# AGENTS.md

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD",
"SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be
interpreted as described in [RFC 2119](https://www.ietf.org/rfc/rfc2119.txt).

## Agent instructions

- `AGENTS.md` is the only agent instructions file; put project rules here. The
  repository MUST NOT contain a `CLAUDE.md` or any other tool-specific copy,
  because a second copy drifts from this one; `make claude-md-check` fails on
  one.

## Command surface

- Run the `Makefile` targets (`make check`, `make fix`, `make test`, ...)
  instead of the underlying tools, so the agent and CI use the same options.
  `make help` lists them.
- Give every new target a `##` help line; `make help` prints it and
  `make help-check` fails on a target without one.

## Gate

- `make check` and `make test` MUST pass before any commit.
- Run `make fix` first for findings it can repair, then edit by hand.

## Commits and branches

- Write commit messages as
  [Conventional Commits](https://www.conventionalcommits.org/) and branch
  names as [Conventional Branch](https://conventionalbranch.org/)
  (`<type>/<description>`, e.g. `feat/add-login`). A pre-commit hook and
  `make commits-check` enforce both; see
  [`docs/conventions/commits-check.md`](docs/conventions/commits-check.md).
- Name a documentation or dependency branch `chore/...`: a branch type is not
  a commit type, and `docs/` is not one.

## Pull requests

Once a pull request is open, the agent MUST:

1. Wait for CI; while it fails, fix the cause, push to the same branch and
   wait again until it passes.
2. Squash-merge a pull request with exactly one commit and use a regular merge
   commit otherwise (`gh pr view --json commits` gives the count).
3. Delete the branch on the remote and locally.
4. Switch back to the base branch, pull it and run `git fetch --prune`.

## Versioning and releases

- Bump the version with each change, as
  [`docs/conventions/versioning.md`](docs/conventions/versioning.md) defines,
  in its own `chore(release)` commit within the same pull request.
- Tag only a minor or major bump, after its pull request merges. Tag a patch
  only when asked to publish it.
- Suggest a GitHub Release after tagging; create one only when asked.

## Documentation

- Write documentation as an OKF bundle of atomic notes under `docs/`: one
  Markdown concept per file, with YAML frontmatter (`type`, `title`,
  `description`).
- Add a new note to its directory's `index.md` and, by file name, to
  [`docs/log.md`](docs/log.md).
- Write a note only when it explains something a reader cannot already get
  from `make help`, a linter's own message, or the configuration it comes
  from.

## Dependencies

- Add a new tool to the ecosystem manager that owns it; use `mise.toml` only
  for a tool that bootstraps an ecosystem or has no manager in this
  repository. See
  [`docs/toolchain/layering-rule.md`](docs/toolchain/layering-rule.md).

## Python

- Write no docstrings on functions, methods or classes; add a comment only
  where the *why* is not obvious from the code. `pylint-gajaguar`'s
  `gajaguar-no-docstrings` fails `make check` on any docstring.
- Enable the plugin with `enable = ["gajaguar"]` in `pyproject.toml`'s
  `[tool.pylint."messages control"]`, not with a list of rules, so a rule
  added by a `pylint-gajaguar` upgrade runs without a config change.
- Keep `pyproject.toml` to settings that differ from the tool's default, and
  keep a `lint.per-file-ignores` entry only while it matches a current
  violation; see
  [`docs/python/pyproject-defaults.md`](docs/python/pyproject-defaults.md).
- Tag a minor or major bump with `make release-tag` after its pull request
  merges: it tags the base branch as `v<project.version>` and pushes the tag.

## Publishing to PyPI

- Publish only when asked: suggest a release after tagging a minor or major
  bump, and create the GitHub Release from the `vX.Y.Z` tag only on request.
- Approve the `pypi` environment's deployment only on request; follow
  [`docs/release/pypi-trusted-publishing.md`](docs/release/pypi-trusted-publishing.md).

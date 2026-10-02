---
okf_version: "0.2"
---

# Documentation

This is an [Open Knowledge Format](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md)
(OKF) bundle: one Markdown concept per file, each with YAML frontmatter, laid
out under this directory.

## Reference

* [Architecture](architecture/index.md) - the layers, the output formats and
  the exit codes.
* [Authentication](auth/index.md) - the credential kinds and how to set up an
  OAuth consumer.
* [Conventions](conventions/index.md) - commit and branch naming, how they're
  enforced, and versioning.
* [Toolchain](toolchain/index.md) - which layer (mise or an ecosystem
  package manager) installs which tool, and why.

## Project

* [Roadmap](roadmap.md) - the releases from 0.1.0 to 1.0.0 and what 1.0.0
  freezes.
* [SDK coverage](coverage.md) - each SDK capability, its command, release and
  status.

See [`log.md`](log.md) for the bundle's change history.

## Release

* [Release](release/index.md) - how this project ships new versions to
  PyPI.

## Python

* [Python](python/index.md) - the interpreter source and the
  `pyproject.toml` settings left out on purpose.

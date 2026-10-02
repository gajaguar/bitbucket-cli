# Toolchain

Which layer — mise or an ecosystem package manager — installs which tool,
and why.

* [Toolchain layering rule](layering-rule.md) - mise bootstraps, the
  ecosystem's own package manager installs everything else.
* [Rejected install backends](rejected-install-backends.md) - the mise
  `npm:`/`pipx:` backends and pre-commit-managed environments this rules
  out.
* [The Claude Code plugin](claude-plugin.md) - the plugin and marketplace
  manifests, and the three skills they ship.
* [Re-tag the notes](retag-notes.md) - run `make docs-retag`, review the
  dry run, then write the tags.

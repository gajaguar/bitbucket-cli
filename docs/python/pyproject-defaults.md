---
type: rule
title: pyproject defaults
description: pyproject.toml holds only settings that change a tool's behavior; anything equal to the default is left out.
tags: [python]
status: stable
---

# pyproject defaults

`pyproject.toml` holds only settings that change a tool's behavior. A setting
equal to the tool's default is noise: it hides the real decisions and drifts
when the default moves. Every `lint.per-file-ignores` entry must match at
least one current violation; drop it when the code that needed it goes away.

These are left out on purpose:

| Omitted setting                                | Why it is not needed                                                                                               |
| :--------------------------------------------- | :----------------------------------------------------------------------------------------------------------------- |
| `license-files`                                | hatchling picks up `LICENSE` by default                                                                            |
| `[tool.hatch.build.targets.wheel].packages`    | hatchling auto-detects `src/<normalized project name>`; only set explicitly when the package name diverges from it |
| `[tool.pytest.ini_options].testpaths`          | pytest's default recursion rules already skip `.venv` and `node_modules`                                           |
| `[tool.coverage.run].source`                   | `addopts` passes `--cov=src`                                                                                       |
| `exclude_lines` with `pragma: no cover`        | already a default; `exclude_also` only adds the `__main__` guard                                                   |
| ruff `target-version`                          | inferred from `requires-python`                                                                                    |
| ruff `lint.isort.section-order`                | equal to ruff's default order                                                                                      |
| pyright `exclude` for `.venv` / `node_modules` | pyright excludes `**/.*` and `**/node_modules` by default                                                          |
| pylint `missing-*-docstring` disables          | `disable = ["all"]` already covers them; only the plugin's `gajaguar-*` checkers run                               |
| `[tool.uv]` interpreter settings               | set once in `mise.toml`'s `[env]` — see [Interpreter source](interpreter-source.md)                                |

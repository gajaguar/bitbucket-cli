UV := uv
PYPI_DEPS := pylint-gajaguar conventional-git

# Use the project's own pinned, dev-dependency copy in make commits-check
# (defined in the base Makefile) instead of an ephemeral uvx fetch.
CONVENTIONAL_GIT := $(UV) run conventional-git

LANG_INSTALL_TARGETS    += install-python
LANG_CHECK_TARGETS      += lint format-check typecheck pylint conventional-git-latest
LANG_FIX_TARGETS        += format lint-fix
LANG_FIX_UNSAFE_TARGETS += format lint-fix-unsafe
LANG_TEST_TARGETS       += pytest

##@ Python

install-python: ## Sync Python deps and register the console scripts the project declares
	$(UV) sync $(addprefix --upgrade-package ,$(PYPI_DEPS))
	if grep -q '^\[project\.scripts\]' pyproject.toml; then $(UV) tool install --editable . --force; fi

lint: ## Lint with Ruff — accepts FILES="..." to limit scope
	$(UV) run ruff check --preview $(or $(FILES),.)

format-check: ## Check formatting with Ruff, without writing — accepts FILES="..."
	$(UV) run ruff format --check --preview $(or $(FILES),.)

mypy: ## Type-check with mypy — accepts FILES="..." to limit scope
	$(UV) run mypy $(or $(FILES),.)

pyright: ## Type-check with Pyright — accepts FILES="..." to limit scope
	$(UV) run pyright $(FILES)

typecheck: mypy pyright ## Run both type checkers

pylint: ## Self-lint with this repo's own checkers (see github.com/gajaguar/pylint-gajaguar) — accepts FILES="..."
	$(UV) run pylint $(or $(FILES),src tests)

conventional-git-latest: ## Fail if the installed conventional-git is behind PyPI (skips when PyPI is unreachable)
	@out=$$($(UV) pip list --outdated --format json 2>/dev/null) || { echo 'conventional-git-latest: PyPI unreachable, skipped'; exit 0; }; \
	behind=$$(echo "$$out" | grep -oE '"name":"conventional-git","version":"[^"]+","latest_version":"[^"]+"' || true); \
	test -z "$$behind" || { echo "conventional-git is behind PyPI ($$behind); run make install"; exit 1; }

format: ## Format code with Ruff — accepts FILES="..." to limit scope
	$(UV) run ruff format --preview $(or $(FILES),.)

lint-fix: ## Auto-fix lint issues with Ruff (safe fixes only) — accepts FILES="..."
	$(UV) run ruff check --fix --preview $(or $(FILES),.)

lint-fix-unsafe: ## Auto-fix lint issues with Ruff, including unsafe fixes — accepts FILES="..."
	$(UV) run ruff check --fix --preview --unsafe-fixes $(or $(FILES),.)

pytest: ## Run the test suite — accepts FILES="..." to limit scope
	$(UV) run pytest $(FILES)

coverage: ## Run tests with an HTML coverage report
	$(UV) run pytest --cov-report=html

build: ## Build the sdist and wheel into dist/
	rm -rf dist
	$(UV) build

release-tag: ## Tag the base branch as v<project.version> and push the tag (minor and major bumps)
	@version=$$($(UV) run python -c 'import tomllib; print(tomllib.load(open("pyproject.toml", "rb"))["project"]["version"])'); base=$(BASE:origin/%=%); tag=v$$version; \
	test "$$(git rev-parse --abbrev-ref HEAD)" = "$$base" && test -z "$$(git status --porcelain)" || { echo "release-tag: run it from a clean $$base"; exit 1; }; \
	git fetch --quiet origin && test "$$(git rev-parse HEAD)" = "$$(git rev-parse origin/$$base)" || { echo "release-tag: $$base is not at origin/$$base"; exit 1; }; \
	git rev-parse --quiet --verify "refs/tags/$$tag" >/dev/null && { echo "release-tag: $$tag already exists"; exit 1; }; \
	git tag -a "$$tag" -m "$$tag" && git push origin "$$tag"

.PHONY: install-python lint format-check mypy pyright typecheck pylint conventional-git-latest \
	format lint-fix lint-fix-unsafe pytest coverage build release-tag

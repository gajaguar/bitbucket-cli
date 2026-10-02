from __future__ import annotations

import json
import tomllib
from pathlib import Path
from typing import Final

import pytest

_REPO_ROOT: Final = Path(__file__).resolve().parents[2]
_SKILLS: Final = sorted((_REPO_ROOT / "skills").glob("*/SKILL.md"))


def test_plugin_manifest_version_matches_pyproject() -> None:
    # Arrange
    plugin = json.loads((_REPO_ROOT / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
    pyproject = tomllib.loads((_REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    # Act
    # Assert
    assert plugin == {
        "name": "bitbucket-cli",
        "version": pyproject["project"]["version"],
        "description": "Bitbucket Cloud pull-request, pipeline and repository skills for Claude Code",
        "author": {"name": "G.A.JAGUAR", "email": "dev@gajaguar.com"},
        "license": "MIT",
        "repository": "https://github.com/gajaguar/bitbucket-cli",
        "keywords": ["bitbucket", "atlassian", "git", "pull-request", "pipelines", "cli", "skill"],
    }, ".claude-plugin/plugin.json has drifted from pyproject.toml; bump both together on release"


def test_marketplace_lists_the_plugin() -> None:
    # Arrange
    plugin = json.loads((_REPO_ROOT / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
    marketplace = json.loads((_REPO_ROOT / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8"))
    # Act
    names = [entry["name"] for entry in marketplace["plugins"]]
    # Assert
    assert names == [plugin["name"]]


@pytest.mark.parametrize("skill", _SKILLS, ids=lambda path: path.parent.name)
def test_skill_name_matches_its_directory(skill: Path) -> None:
    # Arrange
    frontmatter = skill.read_text(encoding="utf-8").split("---", 2)[1]
    # Act
    name = next(line.split(":", 1)[1].strip() for line in frontmatter.splitlines() if line.startswith("name:"))
    # Assert
    assert name == skill.parent.name


def test_three_skills_ship() -> None:
    # Arrange
    # Act
    names = [skill.parent.name for skill in _SKILLS]
    # Assert
    assert names == ["bitbucket-cli", "bitbucket-pipelines", "bitbucket-pull-requests"]

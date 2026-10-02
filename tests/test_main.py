from __future__ import annotations

from typing import TYPE_CHECKING

from bitbucket_unofficial_cli.main import main

if TYPE_CHECKING:
    import pytest


def test_main_prints_greeting(capsys: pytest.CaptureFixture[str]) -> None:
    # Arrange
    # Act
    main()
    # Assert
    captured = capsys.readouterr()
    assert captured.out == "hello from bitbucket-cli\n"

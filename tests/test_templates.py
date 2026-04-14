"""Tests for plonecli.templates module."""

from unittest.mock import MagicMock, patch

import pytest

from plonecli.config import PlonecliConfig
from plonecli.templates import (
    ensure_templates_cloned,
    get_template_path,
    get_templates_info,
    update_templates_clone,
)


def test_ensure_templates_cloned_existing(tmp_path):
    """If clone exists, return path without cloning."""
    templates_dir = tmp_path / "templates"
    templates_dir.mkdir()
    (templates_dir / ".git").mkdir()

    config = PlonecliConfig(templates_dir=str(templates_dir))
    result = ensure_templates_cloned(config)
    assert result == templates_dir


@patch("plonecli.templates.subprocess.run")
def test_ensure_templates_cloned_new(mock_run, tmp_path):
    """If clone doesn't exist, git clone is called."""
    templates_dir = tmp_path / "templates"
    config = PlonecliConfig(
        templates_dir=str(templates_dir),
        repo_url="https://example.com/repo",
        repo_branch="main",
    )

    # Simulate git clone creating the directory
    def side_effect(*args, **kwargs):
        templates_dir.mkdir(parents=True, exist_ok=True)
        (templates_dir / ".git").mkdir()
        return MagicMock(returncode=0)

    mock_run.side_effect = side_effect
    result = ensure_templates_cloned(config)

    mock_run.assert_called_once()
    call_args = mock_run.call_args[0][0]
    assert "git" in call_args
    assert "clone" in call_args
    assert "--depth" in call_args
    assert "https://example.com/repo" in call_args


@patch("plonecli.templates.subprocess.run")
def test_update_templates_clone(mock_run, tmp_path):
    templates_dir = tmp_path / "templates"
    templates_dir.mkdir()
    (templates_dir / ".git").mkdir()

    mock_run.return_value = MagicMock(
        returncode=0,
        stdout="Already up to date.",
        stderr="",
    )

    config = PlonecliConfig(templates_dir=str(templates_dir))
    msg = update_templates_clone(config)

    assert "up to date" in msg.lower()
    mock_run.assert_called_once()


def test_get_template_path(tmp_path):
    (tmp_path / "backend_addon").mkdir()
    config = PlonecliConfig(templates_dir=str(tmp_path))
    path = get_template_path("backend_addon", config)
    assert path == tmp_path / "backend_addon"


def test_get_template_path_unknown(tmp_path):
    config = PlonecliConfig(templates_dir=str(tmp_path))
    with pytest.raises(ValueError, match="Unknown template"):
        get_template_path("nonexistent", config)


@patch("plonecli.templates.subprocess.run")
def test_get_templates_info(mock_run, tmp_path):
    templates_dir = tmp_path / "templates"
    templates_dir.mkdir()

    mock_run.return_value = MagicMock(
        returncode=0,
        stdout="abc1234 2026-04-07 12:00:00 +0000",
        stderr="",
    )

    config = PlonecliConfig(templates_dir=str(templates_dir))
    info = get_templates_info(config)
    assert "abc1234" in info


def test_get_templates_info_not_cloned(tmp_path):
    config = PlonecliConfig(templates_dir=str(tmp_path / "nonexistent"))
    info = get_templates_info(config)
    assert info == "not cloned"

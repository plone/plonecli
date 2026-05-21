"""Tests for the `plonecli skill` command and the skill installer."""

from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from plonecli import skill_installer
from plonecli.cli import cli


@pytest.fixture
def runner():
    return CliRunner()


def test_bundled_skill_present():
    source = skill_installer.get_source_skill_dir()
    assert source.is_dir()
    assert (source / "SKILL.md").is_file()
    assert (source / "reference").is_dir()


def test_install_creates_agents_and_claude(tmp_path):
    base, actions = skill_installer.install_skill(
        scope="project", project_root=tmp_path
    )
    assert base == tmp_path

    agents = tmp_path / ".agents" / "skills" / "plonecli"
    claude = tmp_path / ".claude" / "skills" / "plonecli"

    # canonical copy is real files
    assert (agents / "SKILL.md").is_file()
    # claude alias is a symlink resolving to the same SKILL.md
    assert claude.is_symlink()
    assert (claude / "SKILL.md").read_text() == (agents / "SKILL.md").read_text()

    kinds = {a.kind for a in actions}
    assert kinds == {"copy", "symlink"}


def test_install_refuses_existing_without_force(tmp_path):
    skill_installer.install_skill(scope="project", project_root=tmp_path)
    with pytest.raises(FileExistsError):
        skill_installer.install_skill(scope="project", project_root=tmp_path)


def test_update_overwrites_existing(tmp_path):
    skill_installer.install_skill(scope="project", project_root=tmp_path)
    # mutate installed copy, then update should restore it from source
    installed = tmp_path / ".agents" / "skills" / "plonecli" / "SKILL.md"
    installed.write_text("stale")
    skill_installer.install_skill(
        scope="project", project_root=tmp_path, update=True
    )
    assert installed.read_text() != "stale"


def test_copy_only_makes_claude_a_copy(tmp_path):
    skill_installer.install_skill(
        scope="project", project_root=tmp_path, copy_only=True
    )
    claude = tmp_path / ".claude" / "skills" / "plonecli"
    assert claude.is_dir()
    assert not claude.is_symlink()


@patch("plonecli.cli.find_project_root", return_value=None)
@patch("plonecli.cli.load_config")
def test_cli_skill_install(mock_config, mock_project, runner, tmp_path):
    mock_config.return_value = MagicMock(templates_dir="/tmp/nonexistent")
    with runner.isolated_filesystem(temp_dir=tmp_path) as fs:
        result = runner.invoke(cli, ["skill", "install", "--scope", "project"])
        assert result.exit_code == 0, result.output
        assert "Installed plonecli skill" in result.output
        from pathlib import Path

        assert (Path(fs) / ".agents" / "skills" / "plonecli" / "SKILL.md").is_file()


@patch("plonecli.cli.find_project_root", return_value=None)
@patch("plonecli.cli.load_config")
def test_cli_skill_install_defaults_to_user_scope(
    mock_config, mock_project, runner, tmp_path, monkeypatch
):
    """No --scope must install into the user home, not the current directory."""
    from pathlib import Path

    mock_config.return_value = MagicMock(templates_dir="/tmp/nonexistent")
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
    with runner.isolated_filesystem(temp_dir=tmp_path) as fs:
        result = runner.invoke(cli, ["skill", "install"])
        assert result.exit_code == 0, result.output
        assert (tmp_path / ".agents" / "skills" / "plonecli" / "SKILL.md").is_file()
        assert not (Path(fs) / ".agents").exists()


@patch("plonecli.cli.find_project_root", return_value=None)
@patch("plonecli.cli.load_config")
def test_cli_skill_install_force_after_action(
    mock_config, mock_project, runner, tmp_path
):
    """`--force` must work after the action despite the chained parent group."""
    mock_config.return_value = MagicMock(templates_dir="/tmp/nonexistent")
    with runner.isolated_filesystem(temp_dir=tmp_path):
        assert (
            runner.invoke(cli, ["skill", "install", "--scope", "project"]).exit_code
            == 0
        )
        result = runner.invoke(cli, ["skill", "install", "--scope", "project", "--force"])
        assert result.exit_code == 0, result.output
        assert "Installed plonecli skill" in result.output


@patch("plonecli.cli.find_project_root", return_value=None)
@patch("plonecli.cli.load_config")
def test_cli_skill_install_twice_errors(mock_config, mock_project, runner, tmp_path):
    mock_config.return_value = MagicMock(templates_dir="/tmp/nonexistent")
    with runner.isolated_filesystem(temp_dir=tmp_path):
        first = runner.invoke(cli, ["skill", "install", "--scope", "project"])
        assert first.exit_code == 0
        result = runner.invoke(cli, ["skill", "install", "--scope", "project"])
        assert result.exit_code != 0
        assert "already installed" in result.output

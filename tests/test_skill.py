"""Tests for the `plonecli skill` command and the skill installer."""

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from plonecli import skill_installer
from plonecli.cli import cli
from plonecli.git import dirty_files


def _git(path, *args):
    subprocess.run(["git", "-C", str(path), *args], check=True, capture_output=True)


def _init_repo(path):
    subprocess.run(["git", "init", "-q", str(path)], check=True)
    _git(path, "config", "user.name", "Test")
    _git(path, "config", "user.email", "test@example.org")


def _log(path):
    return subprocess.run(
        ["git", "-C", str(path), "log", "--pretty=%s"],
        capture_output=True,
        text=True,
    ).stdout.splitlines()


def test_bundled_skills_present():
    names = skill_installer.bundled_skill_names()
    assert "plonecli" in names
    assert "plone-schema-fields" in names
    root = skill_installer.get_source_skills_root()
    for name in names:
        assert (root / name / "SKILL.md").is_file()
    assert (root / "plonecli" / "reference").is_dir()


def test_skill_descriptions_stay_short():
    import re

    root = skill_installer.get_source_skills_root()
    for name in skill_installer.bundled_skill_names():
        text = (root / name / "SKILL.md").read_text()
        desc = re.search(r"^description: (.+)$", text, re.M).group(1)
        assert len(desc) <= 500, f"{name} description is {len(desc)} chars"


def test_install_creates_agents_and_claude(tmp_path):
    base, actions = skill_installer.install_skill(
        scope="project", project_root=tmp_path
    )
    assert base == tmp_path

    for name in skill_installer.bundled_skill_names():
        agents = tmp_path / ".agents" / "skills" / name
        claude = tmp_path / ".claude" / "skills" / name

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
    skill_installer.install_skill(scope="project", project_root=tmp_path, update=True)
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
        assert "Installed plonecli skills" in result.output
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
        result = runner.invoke(
            cli, ["skill", "install", "--scope", "project", "--force"]
        )
        assert result.exit_code == 0, result.output
        assert "Installed plonecli skills" in result.output


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


def _project_config(**kwargs):
    return MagicMock(
        templates_dir="/tmp/nonexistent",
        author_name="Test",
        author_email="test@example.org",
        **kwargs,
    )


@patch("plonecli.cli.find_project_root", return_value=None)
@patch("plonecli.cli.load_config")
def test_cli_skill_install_project_scope_commits(
    mock_config, mock_project, runner, tmp_path
):
    """A project install must leave the repo clean, not blocking the next add."""
    mock_config.return_value = _project_config(auto_commit=True)
    with runner.isolated_filesystem(temp_dir=tmp_path) as fs:
        _init_repo(fs)
        result = runner.invoke(cli, ["skill", "install", "--scope", "project"])

        assert result.exit_code == 0, result.output
        assert "Committed: Add plonecli skills" in result.output
        assert _log(fs) == ["Add plonecli skills"]
        assert dirty_files(Path(fs)) == ([], [])


@patch("plonecli.cli.find_project_root", return_value=None)
@patch("plonecli.cli.load_config")
def test_cli_skill_update_project_scope_commits(
    mock_config, mock_project, runner, tmp_path
):
    mock_config.return_value = _project_config(auto_commit=True)
    with runner.isolated_filesystem(temp_dir=tmp_path) as fs:
        _init_repo(fs)
        assert (
            runner.invoke(cli, ["skill", "install", "--scope", "project"]).exit_code
            == 0
        )
        # A drifted installed copy, committed as it stands: the update has
        # something real to restore and therefore something to commit.
        (Path(fs) / ".agents" / "skills" / "plonecli" / "SKILL.md").write_text("stale")
        _git(fs, "commit", "-qam", "Local edit")

        result = runner.invoke(cli, ["skill", "update", "--scope", "project"])

        assert result.exit_code == 0, result.output
        assert _log(fs)[0] == "Update plonecli skills"
        assert dirty_files(Path(fs)) == ([], [])


@pytest.mark.parametrize(
    "args,config_kwargs",
    [
        (["--no-git"], {"auto_commit": True}),
        ([], {"auto_commit": False}),
    ],
)
@patch("plonecli.cli.find_project_root", return_value=None)
@patch("plonecli.cli.load_config")
def test_cli_skill_install_can_opt_out_of_the_commit(
    mock_config, mock_project, runner, tmp_path, args, config_kwargs
):
    mock_config.return_value = _project_config(**config_kwargs)
    with runner.isolated_filesystem(temp_dir=tmp_path) as fs:
        _init_repo(fs)
        result = runner.invoke(cli, ["skill", "install", "--scope", "project", *args])

        assert result.exit_code == 0, result.output
        assert _log(fs) == []
        assert dirty_files(Path(fs)) == ([], [".agents/", ".claude/"])


@patch("plonecli.cli.find_project_root", return_value=None)
@patch("plonecli.cli.load_config")
def test_cli_skill_install_user_scope_does_not_commit(
    mock_config, mock_project, runner, tmp_path, monkeypatch
):
    """User scope writes into ``$HOME``; that is not a plonecli project."""
    mock_config.return_value = _project_config(auto_commit=True)
    home = tmp_path / "home"
    home.mkdir()
    _init_repo(home)
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: home))

    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(cli, ["skill", "install"])

        assert result.exit_code == 0, result.output
        assert _log(home) == []

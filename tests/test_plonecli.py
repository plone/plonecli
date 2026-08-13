"""Tests for plonecli CLI commands."""

import subprocess
from unittest.mock import MagicMock, patch

import pytest

from plonecli.cli import cli
from tests.helpers import project_at


@patch("plonecli.cli.find_project_root", return_value=None)
@patch("plonecli.cli.load_config")
def test_cli_help(mock_config, mock_project, runner):
    mock_config.return_value = MagicMock(templates_dir="/tmp/nonexistent")
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "Plone Command Line Interface" in result.output


@patch("plonecli.cli.find_project_root", return_value=None)
@patch("plonecli.cli.load_config")
def test_cli_versions(mock_config, mock_project, runner):
    mock_config.return_value = MagicMock(templates_dir="/tmp/nonexistent")
    with (
        patch("plonecli.cli.importlib.metadata.version", return_value="3.0.0a1"),
        patch("plonecli.cli.get_templates_info", return_value="abc123 2026-04-07"),
    ):
        result = runner.invoke(cli, ["-V"])
        assert "3.0.0a1" in result.output
        assert "abc123" in result.output


def _make_template(tmp_path, name, plonecli_meta):
    d = tmp_path / name
    d.mkdir()
    lines = ["_plonecli:"]
    for key, value in plonecli_meta.items():
        if isinstance(value, list):
            lines.append(f"  {key}:")
            for v in value:
                lines.append(f"    - {v}")
        else:
            lines.append(f"  {key}: {value}")
    (d / "copier.yml").write_text("\n".join(lines) + "\n")


@patch("plonecli.cli.find_project_root", return_value=None)
@patch("plonecli.cli.load_config")
def test_cli_list_templates(mock_config, mock_project, runner, tmp_path):
    # Set up mock templates dir as an existing clone (has .git)
    (tmp_path / ".git").mkdir()
    _make_template(tmp_path, "backend_addon", {"type": "main", "aliases": ["addon"]})
    _make_template(tmp_path, "zope-setup", {"type": "main"})
    _make_template(tmp_path, "behavior", {"type": "sub", "parent": "backend_addon"})
    _make_template(tmp_path, "content_type", {"type": "sub", "parent": "backend_addon"})

    mock_config.return_value = MagicMock(templates_dir=str(tmp_path))
    result = runner.invoke(cli, ["-l"])
    assert "Available templates:" in result.output
    assert "backend_addon" in result.output


@patch("plonecli.cli.find_project_root", return_value=None)
@patch("plonecli.cli.load_config")
def test_create_help_shows_templates(mock_config, mock_project, runner, tmp_path):
    _make_template(tmp_path, "backend_addon", {"type": "main"})
    _make_template(tmp_path, "zope-setup", {"type": "main"})
    _make_template(
        tmp_path,
        "addon",
        {
            "type": "composite",
            "templates": ["backend_addon", "zope-setup"],
            "aliases": ["add-on"],
        },
    )

    mock_config.return_value = MagicMock(templates_dir=str(tmp_path))
    result = runner.invoke(cli, ["create", "-h"])
    assert result.exit_code == 0
    assert "Templates:" in result.output
    assert "addon" in result.output
    assert "backend_addon" in result.output
    assert "zope-setup" in result.output


@patch("plonecli.cli.find_project_root", return_value=None)
@patch("plonecli.cli.load_config")
@patch("plonecli.cli.run_create")
@patch("plonecli.cli.ensure_templates_cloned")
def test_create_command(
    mock_ensure, mock_run_create, mock_config, mock_project, runner, tmp_path
):
    _make_template(tmp_path, "backend_addon", {"type": "main", "aliases": ["addon"]})
    _make_template(tmp_path, "zope-setup", {"type": "main"})

    mock_config.return_value = MagicMock(templates_dir=str(tmp_path))
    result = runner.invoke(cli, ["create", "addon", "my.addon"])

    assert result.exit_code == 0
    mock_run_create.assert_called_once()
    call_args = mock_run_create.call_args
    assert call_args[0][0] == "backend_addon"
    assert call_args[0][1] == "my.addon"


@patch("plonecli.cli.find_project_root", return_value=None)
@patch("plonecli.cli.load_config")
@patch("plonecli.cli.run_create")
@patch("plonecli.cli.ensure_templates_cloned")
def test_create_composite_template(
    mock_ensure, mock_run_create, mock_config, mock_project, runner, tmp_path
):
    _make_template(tmp_path, "backend_addon", {"type": "main"})
    _make_template(tmp_path, "zope-setup", {"type": "main"})
    _make_template(
        tmp_path,
        "addon",
        {
            "type": "composite",
            "templates": ["backend_addon", "zope-setup"],
            "aliases": ["add-on"],
        },
    )

    mock_config.return_value = MagicMock(templates_dir=str(tmp_path))
    result = runner.invoke(cli, ["create", "addon", "my.addon"])

    assert result.exit_code == 0
    assert mock_run_create.call_count == 2
    calls = mock_run_create.call_args_list
    assert calls[0][0][0] == "backend_addon"
    assert calls[0][0][1] == "my.addon"
    assert calls[1][0][0] == "zope-setup"
    assert calls[1][0][1] == "my.addon"
    # First layer creates fresh files; later layers overlay and must overwrite.
    assert calls[0].kwargs["overwrite"] is False
    assert calls[1].kwargs["overwrite"] is True


@patch("plonecli.cli.find_project_root", return_value=None)
@patch("plonecli.cli.load_config")
@patch("plonecli.cli.run_create")
@patch("plonecli.cli.ensure_templates_cloned")
def test_create_composite_via_alias(
    mock_ensure, mock_run_create, mock_config, mock_project, runner, tmp_path
):
    _make_template(tmp_path, "backend_addon", {"type": "main"})
    _make_template(tmp_path, "zope-setup", {"type": "main"})
    _make_template(
        tmp_path,
        "addon",
        {
            "type": "composite",
            "templates": ["backend_addon", "zope-setup"],
            "aliases": ["add-on"],
        },
    )

    mock_config.return_value = MagicMock(templates_dir=str(tmp_path))
    result = runner.invoke(cli, ["create", "add-on", "my.addon"])

    assert result.exit_code == 0
    assert mock_run_create.call_count == 2


@patch("plonecli.cli.find_project_root")
@patch("plonecli.cli.load_config")
@patch("plonecli.cli.run_create")
@patch("plonecli.cli.ensure_templates_cloned")
def test_create_then_setup_chain_refreshes_project(
    mock_ensure,
    mock_run_create,
    mock_config,
    mock_project,
    runner,
    tmp_path,
):
    _make_template(tmp_path, "backend_addon", {"type": "main"})
    target = tmp_path / "my.addon"
    mock_config.return_value = MagicMock(templates_dir=str(tmp_path), auto_commit=False)
    mock_project.side_effect = lambda start=None: (
        project_at(target) if start is not None else None
    )

    result = runner.invoke(
        cli,
        [
            "create",
            "backend_addon",
            str(target),
            "--defaults",
            "setup",
            "--defaults",
        ],
    )

    assert result.exit_code == 0, result.output
    assert [call.args[0] for call in mock_run_create.call_args_list] == [
        "backend_addon",
        "zope-setup",
    ]
    assert mock_run_create.call_args_list[1].args[1] == str(target)


@patch("plonecli.cli.find_project_root", return_value=None)
@patch("plonecli.cli.load_config")
def test_create_unknown_template(mock_config, mock_project, runner, tmp_path):
    _make_template(tmp_path, "backend_addon", {"type": "main"})

    mock_config.return_value = MagicMock(templates_dir=str(tmp_path))
    result = runner.invoke(cli, ["create", "nonexistent", "mypackage"])
    assert result.exit_code != 0


@patch("plonecli.cli.find_project_root", return_value=None)
@patch("plonecli.cli.load_config")
@patch("plonecli.cli.run_create")
@patch("plonecli.cli.ensure_templates_cloned")
def test_create_clones_templates_on_first_run(
    mock_ensure, mock_run_create, mock_config, mock_project, runner, tmp_path
):
    """A fresh install must clone before resolving the template, not fail.

    Regression: template resolution reads the local clone, so it has to run
    *after* the clone. Without the auto-clone, ``create`` raised NoSuchValue
    on an empty templates dir and forced a manual ``plonecli update``.
    """
    templates_dir = tmp_path / "clone"
    mock_config.return_value = MagicMock(templates_dir=str(templates_dir))

    # Simulate the first-run clone populating the templates dir.
    def fake_clone(config):
        templates_dir.mkdir(parents=True, exist_ok=True)
        _make_template(templates_dir, "backend_addon", {"type": "main"})

    mock_ensure.side_effect = fake_clone

    result = runner.invoke(cli, ["create", "backend_addon", "my.addon"])

    assert result.exit_code == 0, result.output
    mock_ensure.assert_called_once()
    mock_run_create.assert_called_once()


@patch("plonecli.cli.find_project_root")
@patch("plonecli.cli.load_config")
@patch("plonecli.cli.run_add")
@patch("plonecli.cli.ensure_templates_cloned")
def test_add_command(
    mock_ensure, mock_run_add, mock_config, mock_project, runner, tmp_path
):
    _make_template(tmp_path, "backend_addon", {"type": "main"})
    _make_template(tmp_path, "behavior", {"type": "sub", "parent": "backend_addon"})
    _make_template(tmp_path, "content_type", {"type": "sub", "parent": "backend_addon"})

    mock_config.return_value = MagicMock(templates_dir=str(tmp_path))
    mock_project.return_value = MagicMock(
        root_folder=tmp_path,
        project_type="backend_addon",
        package_name="test.addon",
        package_folder="test/addon",
        settings={},
    )

    result = runner.invoke(cli, ["add", "behavior"])
    assert result.exit_code == 0
    mock_run_add.assert_called_once()


@patch("plonecli.cli.find_project_root")
@patch("plonecli.cli.load_config")
@patch("plonecli.cli.run_add")
@patch("plonecli.cli.ensure_templates_cloned")
def test_add_non_interactive(
    mock_ensure, mock_run_add, mock_config, mock_project, runner, tmp_path
):
    _make_template(tmp_path, "backend_addon", {"type": "main"})
    _make_template(tmp_path, "upgrade_step", {"type": "sub", "parent": "backend_addon"})

    mock_config.return_value = MagicMock(templates_dir=str(tmp_path))
    mock_project.return_value = MagicMock(
        root_folder=tmp_path,
        project_type="backend_addon",
        package_name="test.addon",
        package_folder="test/addon",
        settings={},
    )

    result = runner.invoke(
        cli,
        [
            "add",
            "upgrade_step",
            "--defaults",
            "-d",
            "upgrade_step_title=Reimport viewlets",
            "--data",
            "destination_version=1002",
        ],
    )
    assert result.exit_code == 0
    mock_run_add.assert_called_once()
    kwargs = mock_run_add.call_args.kwargs
    assert kwargs["defaults"] is True
    assert kwargs["data"] == {
        "upgrade_step_title": "Reimport viewlets",
        "destination_version": "1002",
    }


@patch("plonecli.cli.find_project_root")
@patch("plonecli.cli.load_config")
@patch("plonecli.cli.run_add")
@patch("plonecli.cli.ensure_templates_cloned")
def test_add_data_file_merges_with_inline_data(
    mock_ensure, mock_run_add, mock_config, mock_project, runner, tmp_path
):
    _make_template(tmp_path, "backend_addon", {"type": "main"})
    _make_template(tmp_path, "upgrade_step", {"type": "sub", "parent": "backend_addon"})

    data_file = tmp_path / "answers.yml"
    data_file.write_text(
        "upgrade_step_title: From file\nupgrade_step_description: From file\n"
    )

    mock_config.return_value = MagicMock(templates_dir=str(tmp_path))
    mock_project.return_value = MagicMock(
        root_folder=tmp_path,
        project_type="backend_addon",
        package_name="test.addon",
        package_folder="test/addon",
        settings={},
    )

    result = runner.invoke(
        cli,
        [
            "add",
            "upgrade_step",
            "--data-file",
            str(data_file),
            # inline -d overrides the same key from the file
            "-d",
            "upgrade_step_title=Inline wins",
        ],
    )
    assert result.exit_code == 0
    kwargs = mock_run_add.call_args.kwargs
    assert kwargs["data"] == {
        "upgrade_step_title": "Inline wins",
        "upgrade_step_description": "From file",
    }


@patch("plonecli.cli.find_project_root")
@patch("plonecli.cli.load_config")
@patch("plonecli.cli.run_add")
@patch("plonecli.cli.ensure_templates_cloned")
def test_add_data_file_missing_fails(
    mock_ensure, mock_run_add, mock_config, mock_project, runner, tmp_path
):
    _make_template(tmp_path, "backend_addon", {"type": "main"})
    _make_template(tmp_path, "upgrade_step", {"type": "sub", "parent": "backend_addon"})

    mock_config.return_value = MagicMock(templates_dir=str(tmp_path))
    mock_project.return_value = MagicMock(
        root_folder=tmp_path,
        project_type="backend_addon",
        package_name="test.addon",
        package_folder="test/addon",
        settings={},
    )

    result = runner.invoke(
        cli, ["add", "upgrade_step", "--data-file", str(tmp_path / "nope.yml")]
    )
    assert result.exit_code != 0
    mock_run_add.assert_not_called()


@patch("plonecli.cli.find_project_root")
@patch("plonecli.cli.load_config")
@patch("plonecli.cli.run_add")
@patch("plonecli.cli.ensure_templates_cloned")
def test_add_data_without_separator_fails(
    mock_ensure, mock_run_add, mock_config, mock_project, runner, tmp_path
):
    _make_template(tmp_path, "backend_addon", {"type": "main"})
    _make_template(tmp_path, "upgrade_step", {"type": "sub", "parent": "backend_addon"})

    mock_config.return_value = MagicMock(templates_dir=str(tmp_path))
    mock_project.return_value = MagicMock(
        root_folder=tmp_path,
        project_type="backend_addon",
        package_name="test.addon",
        package_folder="test/addon",
        settings={},
    )

    result = runner.invoke(cli, ["add", "upgrade_step", "-d", "no_separator"])
    assert result.exit_code != 0
    mock_run_add.assert_not_called()


@patch("plonecli.cli.find_project_root", return_value=None)
@patch("plonecli.cli.load_config")
@patch("plonecli.cli.run_create")
@patch("plonecli.cli.ensure_templates_cloned")
def test_create_non_interactive(
    mock_ensure, mock_run_create, mock_config, mock_project, runner, tmp_path
):
    _make_template(tmp_path, "backend_addon", {"type": "main"})

    mock_config.return_value = MagicMock(templates_dir=str(tmp_path))
    result = runner.invoke(
        cli,
        ["create", "backend_addon", "my.addon", "--defaults", "-d", "description=Demo"],
    )

    assert result.exit_code == 0
    mock_run_create.assert_called_once()
    kwargs = mock_run_create.call_args.kwargs
    assert kwargs["defaults"] is True
    assert kwargs["data"] == {"description": "Demo"}


@patch("plonecli.cli.find_project_root", return_value=None)
@patch("plonecli.cli.load_config")
@patch("plonecli.cli.run_create")
@patch("plonecli.cli.ensure_templates_cloned")
def test_create_commits_by_default(
    mock_ensure, mock_run_create, mock_config, mock_project, runner, tmp_path
):
    _make_template(tmp_path, "backend_addon", {"type": "main"})
    mock_config.return_value = MagicMock(templates_dir=str(tmp_path), auto_commit=True)

    result = runner.invoke(cli, ["create", "backend_addon", "my.addon"])

    assert result.exit_code == 0
    assert mock_run_create.call_args.kwargs["git_commit"] is True


@patch("plonecli.cli.find_project_root", return_value=None)
@patch("plonecli.cli.load_config")
@patch("plonecli.cli.run_create")
@patch("plonecli.cli.ensure_templates_cloned")
def test_create_no_git_flag(
    mock_ensure, mock_run_create, mock_config, mock_project, runner, tmp_path
):
    _make_template(tmp_path, "backend_addon", {"type": "main"})
    mock_config.return_value = MagicMock(templates_dir=str(tmp_path), auto_commit=True)

    result = runner.invoke(cli, ["create", "backend_addon", "my.addon", "--no-git"])

    assert result.exit_code == 0
    assert mock_run_create.call_args.kwargs["git_commit"] is False


@patch("plonecli.cli.find_project_root", return_value=None)
@patch("plonecli.cli.load_config")
@patch("plonecli.cli.run_create")
@patch("plonecli.cli.ensure_templates_cloned")
def test_create_respects_auto_commit_config(
    mock_ensure, mock_run_create, mock_config, mock_project, runner, tmp_path
):
    _make_template(tmp_path, "backend_addon", {"type": "main"})
    mock_config.return_value = MagicMock(templates_dir=str(tmp_path), auto_commit=False)

    result = runner.invoke(cli, ["create", "backend_addon", "my.addon"])

    assert result.exit_code == 0
    assert mock_run_create.call_args.kwargs["git_commit"] is False


@patch("plonecli.cli.find_project_root")
@patch("plonecli.cli.load_config")
@patch("plonecli.cli.run_add")
@patch("plonecli.cli.ensure_templates_cloned")
def test_add_no_git_flag(
    mock_ensure, mock_run_add, mock_config, mock_project, runner, tmp_path
):
    _make_template(tmp_path, "backend_addon", {"type": "main"})
    _make_template(tmp_path, "behavior", {"type": "sub", "parent": "backend_addon"})
    mock_config.return_value = MagicMock(templates_dir=str(tmp_path), auto_commit=True)
    mock_project.return_value = MagicMock(
        root_folder=tmp_path,
        project_type="backend_addon",
        package_name="test.addon",
        package_folder="test/addon",
        settings={},
    )

    result = runner.invoke(cli, ["add", "behavior", "--no-git"])

    assert result.exit_code == 0
    assert mock_run_add.call_args.kwargs["git_commit"] is False


def _dirty_repo(path):
    """Init a git repo at ``path`` with an uncommitted (untracked) file."""
    subprocess.run(["git", "init"], cwd=str(path), check=True, capture_output=True)
    (path / "wip.txt").write_text("work in progress\n")


@patch("plonecli.cli._is_interactive", return_value=True)
@patch("plonecli.cli.find_project_root")
@patch("plonecli.cli.load_config")
@patch("plonecli.cli.run_add")
@patch("plonecli.cli.ensure_templates_cloned")
def test_add_aborts_on_dirty_repo(
    mock_ensure, mock_run_add, mock_config, mock_project, mock_tty, runner, tmp_path
):
    _make_template(tmp_path, "backend_addon", {"type": "main"})
    _make_template(tmp_path, "behavior", {"type": "sub", "parent": "backend_addon"})
    _dirty_repo(tmp_path)
    mock_config.return_value = MagicMock(templates_dir=str(tmp_path), auto_commit=True)
    mock_project.return_value = project_at(tmp_path)

    result = runner.invoke(cli, ["add", "behavior"], input="n\n")

    assert result.exit_code == 0
    assert "uncommitted changes" in result.output
    assert "Aborted" in result.output
    mock_run_add.assert_not_called()


@patch("plonecli.cli._is_interactive", return_value=True)
@patch("plonecli.cli.find_project_root")
@patch("plonecli.cli.load_config")
@patch("plonecli.cli.run_add")
@patch("plonecli.cli.ensure_templates_cloned")
def test_add_proceeds_when_confirmed_on_dirty_repo(
    mock_ensure, mock_run_add, mock_config, mock_project, mock_tty, runner, tmp_path
):
    _make_template(tmp_path, "backend_addon", {"type": "main"})
    _make_template(tmp_path, "behavior", {"type": "sub", "parent": "backend_addon"})
    _dirty_repo(tmp_path)
    mock_config.return_value = MagicMock(templates_dir=str(tmp_path), auto_commit=True)
    mock_project.return_value = project_at(tmp_path)

    result = runner.invoke(cli, ["add", "behavior"], input="y\n")

    assert result.exit_code == 0
    mock_run_add.assert_called_once()


@patch("plonecli.cli._is_interactive", return_value=True)
@patch("plonecli.cli.find_project_root")
@patch("plonecli.cli.load_config")
@patch("plonecli.cli.run_add")
@patch("plonecli.cli.ensure_templates_cloned")
def test_add_dirty_repo_fails_in_non_interactive_mode(
    mock_ensure, mock_run_add, mock_config, mock_project, mock_tty, runner, tmp_path
):
    """``--defaults`` must not silently mix generated files into dirty work."""
    _make_template(tmp_path, "backend_addon", {"type": "main"})
    _make_template(tmp_path, "upgrade_step", {"type": "sub", "parent": "backend_addon"})
    _dirty_repo(tmp_path)
    mock_config.return_value = MagicMock(templates_dir=str(tmp_path), auto_commit=True)
    mock_project.return_value = project_at(tmp_path)

    result = runner.invoke(
        cli, ["add", "upgrade_step", "--defaults", "-d", "upgrade_step_title=X"]
    )

    assert result.exit_code != 0
    assert "uncommitted changes" in result.output
    assert "--allow-dirty" in result.output
    mock_run_add.assert_not_called()


@patch("plonecli.cli._is_interactive", return_value=False)
@patch("plonecli.cli.find_project_root")
@patch("plonecli.cli.load_config")
@patch("plonecli.cli.run_add")
@patch("plonecli.cli.ensure_templates_cloned")
def test_add_dirty_repo_fails_without_a_tty(
    mock_ensure, mock_run_add, mock_config, mock_project, mock_tty, runner, tmp_path
):
    _make_template(tmp_path, "backend_addon", {"type": "main"})
    _make_template(tmp_path, "behavior", {"type": "sub", "parent": "backend_addon"})
    _dirty_repo(tmp_path)
    mock_config.return_value = MagicMock(templates_dir=str(tmp_path), auto_commit=True)
    mock_project.return_value = project_at(tmp_path)

    result = runner.invoke(cli, ["add", "behavior"])

    assert result.exit_code != 0
    mock_run_add.assert_not_called()


@patch("plonecli.cli._is_interactive", return_value=False)
@patch("plonecli.cli.find_project_root")
@patch("plonecli.cli.load_config")
@patch("plonecli.cli.run_add")
@patch("plonecli.cli.ensure_templates_cloned")
def test_add_allow_dirty_proceeds_non_interactively(
    mock_ensure, mock_run_add, mock_config, mock_project, mock_tty, runner, tmp_path
):
    _make_template(tmp_path, "backend_addon", {"type": "main"})
    _make_template(tmp_path, "upgrade_step", {"type": "sub", "parent": "backend_addon"})
    _dirty_repo(tmp_path)
    mock_config.return_value = MagicMock(templates_dir=str(tmp_path), auto_commit=True)
    mock_project.return_value = project_at(tmp_path)

    result = runner.invoke(
        cli,
        [
            "add",
            "upgrade_step",
            "--defaults",
            "--allow-dirty",
            "-d",
            "upgrade_step_title=X",
        ],
    )

    assert result.exit_code == 0, result.output
    assert "uncommitted changes" in result.output
    mock_run_add.assert_called_once()


@patch("plonecli.cli._is_interactive", return_value=True)
@patch("plonecli.cli.find_project_root")
@patch("plonecli.cli.load_config")
@patch("plonecli.cli.run_add")
@patch("plonecli.cli.ensure_templates_cloned")
def test_add_allow_dirty_skips_the_prompt(
    mock_ensure, mock_run_add, mock_config, mock_project, mock_tty, runner, tmp_path
):
    _make_template(tmp_path, "backend_addon", {"type": "main"})
    _make_template(tmp_path, "behavior", {"type": "sub", "parent": "backend_addon"})
    _dirty_repo(tmp_path)
    mock_config.return_value = MagicMock(templates_dir=str(tmp_path), auto_commit=True)
    mock_project.return_value = project_at(tmp_path)

    # No input supplied: a prompt would abort the run.
    result = runner.invoke(cli, ["add", "behavior", "--allow-dirty"])

    assert result.exit_code == 0, result.output
    mock_run_add.assert_called_once()


@patch("plonecli.cli._is_interactive", return_value=False)
@patch("plonecli.cli.find_project_root", return_value=None)
@patch("plonecli.cli.load_config")
@patch("plonecli.cli.run_create")
@patch("plonecli.cli.ensure_templates_cloned")
def test_create_dirty_target_fails_in_non_interactive_mode(
    mock_ensure, mock_run_create, mock_config, mock_project, mock_tty, runner, tmp_path
):
    _make_template(tmp_path, "backend_addon", {"type": "main"})
    target = tmp_path / "my.addon"
    target.mkdir()
    _dirty_repo(target)
    mock_config.return_value = MagicMock(templates_dir=str(tmp_path), auto_commit=True)

    result = runner.invoke(cli, ["create", "backend_addon", str(target), "--defaults"])

    assert result.exit_code != 0
    assert "--allow-dirty" in result.output
    mock_run_create.assert_not_called()


@patch("plonecli.cli._is_interactive", return_value=False)
@patch("plonecli.cli.find_project_root", return_value=None)
@patch("plonecli.cli.load_config")
@patch("plonecli.cli.run_create")
@patch("plonecli.cli.ensure_templates_cloned")
def test_create_allow_dirty_proceeds(
    mock_ensure, mock_run_create, mock_config, mock_project, mock_tty, runner, tmp_path
):
    _make_template(tmp_path, "backend_addon", {"type": "main"})
    target = tmp_path / "my.addon"
    target.mkdir()
    _dirty_repo(target)
    mock_config.return_value = MagicMock(templates_dir=str(tmp_path), auto_commit=True)

    result = runner.invoke(
        cli, ["create", "backend_addon", str(target), "--defaults", "--allow-dirty"]
    )

    assert result.exit_code == 0, result.output
    mock_run_create.assert_called_once()


@patch("plonecli.cli.find_project_root", return_value=None)
@patch("plonecli.cli.load_config")
def test_add_outside_project(mock_config, mock_project, runner, tmp_path):
    mock_config.return_value = MagicMock(templates_dir=str(tmp_path))
    result = runner.invoke(cli, ["add", "behavior"])
    assert result.exit_code != 0


def _tasks_project(
    path,
    test_params="c, verbose=False, test=None, package=None",
    pyproject=(
        "[project]\nname = 'x'\n\n"
        "[project.optional-dependencies]\ntest = ['pytest']\n\n"
        "[dependency-groups]\ndev = ['invoke']\n"
    ),
):
    """A project whose generated tasks.py exposes the given ``test`` signature."""
    (path / "tasks.py").write_text(
        f'"""Invoke tasks."""\n\n\n@task\ndef test({test_params}):\n    pass\n'
    )
    if pyproject is not None:
        (path / "pyproject.toml").write_text(pyproject)
    return MagicMock(
        root_folder=path,
        project_type="backend_addon",
        settings={},
    )


@patch("plonecli.cli.find_project_root")
@patch("plonecli.cli.load_config")
@patch("plonecli.cli.subprocess.call", return_value=0)
def test_serve_command(mock_call, mock_config, mock_project, runner, tmp_path):
    mock_config.return_value = MagicMock(templates_dir=str(tmp_path))
    mock_project.return_value = _tasks_project(tmp_path)

    result = runner.invoke(cli, ["serve"])
    assert result.exit_code == 0, result.output
    mock_call.assert_called_once()
    call_args = mock_call.call_args[0][0]
    assert call_args == ["uv", "run", "invoke", "start"]


@patch("plonecli.cli.find_project_root")
@patch("plonecli.cli.load_config")
@patch("plonecli.cli.subprocess.call", return_value=0)
def test_test_command(mock_call, mock_config, mock_project, runner, tmp_path):
    mock_config.return_value = MagicMock(templates_dir=str(tmp_path))
    mock_project.return_value = _tasks_project(tmp_path)

    result = runner.invoke(cli, ["test"])
    assert result.exit_code == 0, result.output
    call_args = mock_call.call_args[0][0]
    assert call_args == ["uv", "run", "invoke", "test"]


@patch("plonecli.cli.find_project_root")
@patch("plonecli.cli.load_config")
@patch("plonecli.cli.subprocess.call", return_value=0)
def test_test_command_verbose(mock_call, mock_config, mock_project, runner, tmp_path):
    mock_config.return_value = MagicMock(templates_dir=str(tmp_path))
    mock_project.return_value = _tasks_project(tmp_path)

    result = runner.invoke(cli, ["test", "--verbose"])
    assert result.exit_code == 0, result.output
    call_args = mock_call.call_args[0][0]
    assert "--verbose" in call_args


@patch("plonecli.cli.find_project_root")
@patch("plonecli.cli.load_config")
@patch("plonecli.cli.subprocess.call", return_value=0)
def test_test_command_single_test(
    mock_call, mock_config, mock_project, runner, tmp_path
):
    """``-t`` keeps the edit-test loop fast by running one named test."""
    mock_config.return_value = MagicMock(templates_dir=str(tmp_path))
    mock_project.return_value = _tasks_project(tmp_path)

    result = runner.invoke(cli, ["test", "-t", "test_behavior_installed"])

    assert result.exit_code == 0, result.output
    assert mock_call.call_args[0][0] == [
        "uv",
        "run",
        "invoke",
        "test",
        "--test",
        "test_behavior_installed",
    ]


@patch("plonecli.cli.find_project_root")
@patch("plonecli.cli.load_config")
@patch("plonecli.cli.subprocess.call", return_value=0)
def test_test_command_package_filter(
    mock_call, mock_config, mock_project, runner, tmp_path
):
    mock_config.return_value = MagicMock(templates_dir=str(tmp_path))
    mock_project.return_value = _tasks_project(tmp_path)

    result = runner.invoke(cli, ["test", "-s", "src/collective/todo"])

    assert result.exit_code == 0, result.output
    assert mock_call.call_args[0][0] == [
        "uv",
        "run",
        "invoke",
        "test",
        "--package",
        "src/collective/todo",
    ]


@patch("plonecli.cli.find_project_root")
@patch("plonecli.cli.load_config")
@patch("plonecli.cli.subprocess.call", return_value=0)
def test_test_filters_combine_with_verbose(
    mock_call, mock_config, mock_project, runner, tmp_path
):
    mock_config.return_value = MagicMock(templates_dir=str(tmp_path))
    mock_project.return_value = _tasks_project(tmp_path)

    result = runner.invoke(
        cli, ["test", "-v", "-t", "test_x", "-s", "src/collective/todo"]
    )

    assert result.exit_code == 0, result.output
    call_args = mock_call.call_args[0][0]
    assert "--verbose" in call_args
    assert "--test" in call_args
    assert "--package" in call_args


@patch("plonecli.cli.find_project_root")
@patch("plonecli.cli.load_config")
@patch("plonecli.cli.subprocess.call", return_value=0)
def test_test_filter_on_old_tasks_file_explains_the_fix(
    mock_call, mock_config, mock_project, runner, tmp_path
):
    """A project generated before the task gained the filters must not just
    hand an unknown flag to invoke."""
    mock_config.return_value = MagicMock(templates_dir=str(tmp_path))
    mock_project.return_value = _tasks_project(tmp_path, test_params="c, verbose=False")

    result = runner.invoke(cli, ["test", "-t", "test_x"])

    assert result.exit_code != 0
    assert "--test" in result.output
    assert "tasks.py" in result.output
    mock_call.assert_not_called()


@patch("plonecli.cli.find_project_root")
@patch("plonecli.cli.load_config")
@patch("plonecli.cli.subprocess.call", return_value=0)
def test_test_without_filters_runs_on_old_tasks_file(
    mock_call, mock_config, mock_project, runner, tmp_path
):
    """The signature check only gates the new options."""
    mock_config.return_value = MagicMock(templates_dir=str(tmp_path))
    mock_project.return_value = _tasks_project(tmp_path, test_params="c, verbose=False")

    result = runner.invoke(cli, ["test"])

    assert result.exit_code == 0, result.output
    mock_call.assert_called_once()


@patch("plonecli.cli.find_project_root")
@patch("plonecli.cli.load_config")
@patch("plonecli.cli.subprocess.call", return_value=0)
def test_debug_command(mock_call, mock_config, mock_project, runner, tmp_path):
    mock_config.return_value = MagicMock(templates_dir=str(tmp_path))
    mock_project.return_value = _tasks_project(tmp_path)

    result = runner.invoke(cli, ["debug"])
    assert result.exit_code == 0, result.output
    call_args = mock_call.call_args[0][0]
    assert call_args == ["uv", "run", "invoke", "debug"]


@pytest.mark.parametrize("command", ["serve", "test", "debug"])
@patch("plonecli.cli.find_project_root")
@patch("plonecli.cli.load_config")
@patch("plonecli.cli.subprocess.call", return_value=0)
def test_task_commands_explain_missing_tasks_file(
    mock_call, mock_config, mock_project, runner, tmp_path, command
):
    """Without tasks.py there is no invoke tooling; say so instead of failing
    inside a subprocess."""
    mock_config.return_value = MagicMock(templates_dir=str(tmp_path))
    mock_project.return_value = MagicMock(
        root_folder=tmp_path,
        project_type="backend_addon",
        settings={},
    )

    result = runner.invoke(cli, [command])

    assert result.exit_code != 0
    assert "tasks.py" in result.output
    assert "plonecli setup" in result.output
    mock_call.assert_not_called()


@pytest.mark.parametrize("command", ["serve", "test", "debug"])
@patch("plonecli.cli.shutil.which", return_value=None)
@patch("plonecli.cli.find_project_root")
@patch("plonecli.cli.load_config")
@patch("plonecli.cli.subprocess.call", return_value=0)
def test_task_commands_explain_missing_uv(
    mock_call, mock_config, mock_project, mock_which, runner, tmp_path, command
):
    mock_config.return_value = MagicMock(templates_dir=str(tmp_path))
    mock_project.return_value = _tasks_project(tmp_path)

    result = runner.invoke(cli, [command])

    assert result.exit_code != 0
    assert "uv" in result.output
    mock_call.assert_not_called()


@pytest.mark.parametrize("command", ["serve", "test", "debug"])
@patch("plonecli.cli.find_project_root")
@patch("plonecli.cli.load_config")
@patch("plonecli.cli.subprocess.call", return_value=0)
def test_task_commands_explain_undeclared_invoke(
    mock_call, mock_config, mock_project, runner, tmp_path, command
):
    """``uv run invoke`` dies with "Failed to spawn: invoke" if the project does
    not declare invoke, so name the dependency group instead."""
    mock_config.return_value = MagicMock(templates_dir=str(tmp_path))
    mock_project.return_value = _tasks_project(
        tmp_path,
        pyproject="[project]\nname = 'x'\n\n"
        "[project.optional-dependencies]\ntest = ['pytest']\n",
    )

    result = runner.invoke(cli, [command])

    assert result.exit_code != 0
    assert "invoke" in result.output
    assert "dev" in result.output
    mock_call.assert_not_called()


@patch("plonecli.cli.find_project_root")
@patch("plonecli.cli.load_config")
@patch("plonecli.cli.subprocess.call", return_value=0)
def test_test_command_explains_undeclared_pytest(
    mock_call, mock_config, mock_project, runner, tmp_path
):
    """The generated task runs ``uv run --extra test pytest``, so name that extra."""
    mock_config.return_value = MagicMock(templates_dir=str(tmp_path))
    mock_project.return_value = _tasks_project(
        tmp_path,
        pyproject="[project]\nname = 'x'\n\n[dependency-groups]\ndev = ['invoke']\n",
    )

    result = runner.invoke(cli, ["test"])

    assert result.exit_code != 0
    assert "pytest" in result.output
    assert "test" in result.output
    mock_call.assert_not_called()


@pytest.mark.parametrize("command", ["serve", "debug"])
@patch("plonecli.cli.find_project_root")
@patch("plonecli.cli.load_config")
@patch("plonecli.cli.subprocess.call", return_value=0)
def test_serve_and_debug_do_not_need_pytest(
    mock_call, mock_config, mock_project, runner, tmp_path, command
):
    mock_config.return_value = MagicMock(templates_dir=str(tmp_path))
    mock_project.return_value = _tasks_project(
        tmp_path,
        pyproject="[project]\nname = 'x'\n\n[dependency-groups]\ndev = ['invoke']\n",
    )

    result = runner.invoke(cli, [command])

    assert result.exit_code == 0, result.output
    mock_call.assert_called_once()


@pytest.mark.parametrize("command", ["serve", "test", "debug"])
@patch("plonecli.cli.find_project_root")
@patch("plonecli.cli.load_config")
@patch("plonecli.cli.subprocess.call", return_value=0)
def test_unreadable_pyproject_does_not_block_the_run(
    mock_call, mock_config, mock_project, runner, tmp_path, command
):
    """With no basis to judge the dependencies, defer to uv rather than guess."""
    mock_config.return_value = MagicMock(templates_dir=str(tmp_path))
    mock_project.return_value = _tasks_project(tmp_path, pyproject="[project\nbroken")

    result = runner.invoke(cli, [command])

    assert result.exit_code == 0, result.output
    mock_call.assert_called_once()


@pytest.mark.parametrize(
    "requirement",
    ["invoke", "invoke>=2.0", "Invoke", "invoke[extra]>=2 ; python_version>'3.10'"],
)
@patch("plonecli.cli.find_project_root")
@patch("plonecli.cli.load_config")
@patch("plonecli.cli.subprocess.call", return_value=0)
def test_invoke_recognised_in_any_requirement_form(
    mock_call, mock_config, mock_project, runner, tmp_path, requirement
):
    mock_config.return_value = MagicMock(templates_dir=str(tmp_path))
    mock_project.return_value = _tasks_project(
        tmp_path,
        pyproject=f'[project]\nname = "x"\ndependencies = ["{requirement}"]\n',
    )

    result = runner.invoke(cli, ["serve"])

    assert result.exit_code == 0, result.output
    mock_call.assert_called_once()


@patch("plonecli.cli.find_project_root")
@patch("plonecli.cli.load_config")
@patch("plonecli.cli.subprocess.call", return_value=1)
def test_test_command_propagates_a_failing_exit_code(
    mock_call, mock_config, mock_project, runner, tmp_path
):
    """Failing tests must fail the CLI, so scripts and CI notice."""
    mock_config.return_value = MagicMock(templates_dir=str(tmp_path))
    mock_project.return_value = _tasks_project(tmp_path)

    result = runner.invoke(cli, ["test"])

    assert result.exit_code == 1

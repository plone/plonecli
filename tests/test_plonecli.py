"""Tests for plonecli CLI commands."""

from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from plonecli.cli import cli


@pytest.fixture
def runner():
    return CliRunner()


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
    with patch("plonecli.cli.importlib.metadata.version", return_value="3.0.0a1"):
        with patch("plonecli.cli.get_templates_info", return_value="abc123 2026-04-07"):
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
    # Set up mock templates dir
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
        {"type": "composite", "templates": ["backend_addon", "zope-setup"], "aliases": ["add-on"]},
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
def test_create_command(mock_ensure, mock_run_create, mock_config, mock_project, runner, tmp_path):
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
def test_create_composite_template(mock_ensure, mock_run_create, mock_config, mock_project, runner, tmp_path):
    _make_template(tmp_path, "backend_addon", {"type": "main"})
    _make_template(tmp_path, "zope-setup", {"type": "main"})
    _make_template(
        tmp_path,
        "addon",
        {"type": "composite", "templates": ["backend_addon", "zope-setup"], "aliases": ["add-on"]},
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


@patch("plonecli.cli.find_project_root", return_value=None)
@patch("plonecli.cli.load_config")
@patch("plonecli.cli.run_create")
@patch("plonecli.cli.ensure_templates_cloned")
def test_create_composite_via_alias(mock_ensure, mock_run_create, mock_config, mock_project, runner, tmp_path):
    _make_template(tmp_path, "backend_addon", {"type": "main"})
    _make_template(tmp_path, "zope-setup", {"type": "main"})
    _make_template(
        tmp_path,
        "addon",
        {"type": "composite", "templates": ["backend_addon", "zope-setup"], "aliases": ["add-on"]},
    )

    mock_config.return_value = MagicMock(templates_dir=str(tmp_path))
    result = runner.invoke(cli, ["create", "add-on", "my.addon"])

    assert result.exit_code == 0
    assert mock_run_create.call_count == 2


@patch("plonecli.cli.find_project_root", return_value=None)
@patch("plonecli.cli.load_config")
def test_create_unknown_template(mock_config, mock_project, runner, tmp_path):
    _make_template(tmp_path, "backend_addon", {"type": "main"})

    mock_config.return_value = MagicMock(templates_dir=str(tmp_path))
    result = runner.invoke(cli, ["create", "nonexistent", "mypackage"])
    assert result.exit_code != 0


@patch("plonecli.cli.find_project_root")
@patch("plonecli.cli.load_config")
@patch("plonecli.cli.run_add")
@patch("plonecli.cli.ensure_templates_cloned")
def test_add_command(mock_ensure, mock_run_add, mock_config, mock_project, runner, tmp_path):
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
def test_add_outside_project(mock_config, mock_project, runner, tmp_path):
    mock_config.return_value = MagicMock(templates_dir=str(tmp_path))
    result = runner.invoke(cli, ["add", "behavior"])
    assert result.exit_code != 0


@patch("plonecli.cli.find_project_root")
@patch("plonecli.cli.load_config")
@patch("plonecli.cli.subprocess.call", return_value=0)
def test_serve_command(mock_call, mock_config, mock_project, runner, tmp_path):
    mock_config.return_value = MagicMock(templates_dir=str(tmp_path))
    mock_project.return_value = MagicMock(
        root_folder=tmp_path,
        project_type="zope-setup",
        settings={},
    )

    result = runner.invoke(cli, ["serve"])
    assert result.exit_code == 0
    mock_call.assert_called_once()
    call_args = mock_call.call_args[0][0]
    assert call_args == ["uv", "run", "invoke", "start"]


@patch("plonecli.cli.find_project_root")
@patch("plonecli.cli.load_config")
@patch("plonecli.cli.subprocess.call", return_value=0)
def test_test_command(mock_call, mock_config, mock_project, runner, tmp_path):
    mock_config.return_value = MagicMock(templates_dir=str(tmp_path))
    mock_project.return_value = MagicMock(
        root_folder=tmp_path,
        project_type="backend_addon",
        settings={},
    )

    result = runner.invoke(cli, ["test"])
    assert result.exit_code == 0
    call_args = mock_call.call_args[0][0]
    assert call_args == ["uv", "run", "invoke", "test"]


@patch("plonecli.cli.find_project_root")
@patch("plonecli.cli.load_config")
@patch("plonecli.cli.subprocess.call", return_value=0)
def test_test_command_verbose(mock_call, mock_config, mock_project, runner, tmp_path):
    mock_config.return_value = MagicMock(templates_dir=str(tmp_path))
    mock_project.return_value = MagicMock(
        root_folder=tmp_path,
        project_type="backend_addon",
        settings={},
    )

    result = runner.invoke(cli, ["test", "--verbose"])
    assert result.exit_code == 0
    call_args = mock_call.call_args[0][0]
    assert "--verbose" in call_args


@patch("plonecli.cli.find_project_root")
@patch("plonecli.cli.load_config")
@patch("plonecli.cli.subprocess.call", return_value=0)
def test_debug_command(mock_call, mock_config, mock_project, runner, tmp_path):
    mock_config.return_value = MagicMock(templates_dir=str(tmp_path))
    mock_project.return_value = MagicMock(
        root_folder=tmp_path,
        project_type="zope-setup",
        settings={},
    )

    result = runner.invoke(cli, ["debug"])
    assert result.exit_code == 0
    call_args = mock_call.call_args[0][0]
    assert call_args == ["uv", "run", "invoke", "debug"]

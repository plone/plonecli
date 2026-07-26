"""CLI-level tests for the ``plonecli setup`` command."""

from unittest.mock import MagicMock, patch

from plonecli.cli import cli
from tests.helpers import project_at


@patch("plonecli.cli.find_project_root", return_value=None)
@patch("plonecli.cli.load_config")
def test_setup_outside_project_fails(mock_config, mock_project, runner, tmp_path):
    mock_config.return_value = MagicMock(templates_dir=str(tmp_path))

    result = runner.invoke(cli, ["setup"])

    assert result.exit_code != 0


@patch("plonecli.cli.find_project_root")
@patch("plonecli.cli.load_config")
@patch("plonecli.cli.run_create")
def test_setup_rejects_non_backend_addon(
    mock_run_create, mock_config, mock_project, runner, tmp_path
):
    mock_config.return_value = MagicMock(templates_dir=str(tmp_path))
    mock_project.return_value = project_at(tmp_path, project_type="zope-setup")

    result = runner.invoke(cli, ["setup"])

    assert result.exit_code != 0
    assert "backend_addon" in result.output
    mock_run_create.assert_not_called()


@patch("plonecli.cli.find_project_root")
@patch("plonecli.cli.load_config")
@patch("plonecli.cli.run_create")
def test_setup_runs_zope_setup_with_overwrite(
    mock_run_create, mock_config, mock_project, runner, tmp_path
):
    mock_config.return_value = MagicMock(templates_dir=str(tmp_path))
    mock_project.return_value = project_at(tmp_path)

    result = runner.invoke(cli, ["setup"])

    assert result.exit_code == 0, result.output
    mock_run_create.assert_called_once()
    args = mock_run_create.call_args[0]
    assert args[0] == "zope-setup"
    assert args[1] == str(tmp_path)
    assert mock_run_create.call_args.kwargs["overwrite"] is True


@patch("plonecli.cli.find_project_root")
@patch("plonecli.cli.load_config")
@patch("plonecli.cli.run_create")
def test_setup_non_interactive(
    mock_run_create, mock_config, mock_project, runner, tmp_path
):
    """A backend addon can be bootstrapped end to end from a script."""
    mock_config.return_value = MagicMock(templates_dir=str(tmp_path))
    mock_project.return_value = project_at(tmp_path)

    result = runner.invoke(
        cli,
        ["setup", "--defaults", "-d", "plone_version=6.1.1", "-d", "db_storage=zeo"],
    )

    assert result.exit_code == 0, result.output
    kwargs = mock_run_create.call_args.kwargs
    assert kwargs["defaults"] is True
    assert kwargs["data"] == {"plone_version": "6.1.1", "db_storage": "zeo"}


@patch("plonecli.cli.find_project_root")
@patch("plonecli.cli.load_config")
@patch("plonecli.cli.run_create")
def test_setup_data_file_merges_with_inline_data(
    mock_run_create, mock_config, mock_project, runner, tmp_path
):
    data_file = tmp_path / "answers.yml"
    data_file.write_text("plone_version: 6.0.13\ndb_storage: relstorage\n")
    mock_config.return_value = MagicMock(templates_dir=str(tmp_path))
    mock_project.return_value = project_at(tmp_path)

    result = runner.invoke(
        cli,
        ["setup", "--data-file", str(data_file), "-d", "plone_version=6.1.1"],
    )

    assert result.exit_code == 0, result.output
    assert mock_run_create.call_args.kwargs["data"] == {
        "plone_version": "6.1.1",
        "db_storage": "relstorage",
    }


@patch("plonecli.cli.find_project_root")
@patch("plonecli.cli.load_config")
@patch("plonecli.cli.run_create")
def test_setup_data_without_separator_fails(
    mock_run_create, mock_config, mock_project, runner, tmp_path
):
    mock_config.return_value = MagicMock(templates_dir=str(tmp_path))
    mock_project.return_value = project_at(tmp_path)

    result = runner.invoke(cli, ["setup", "-d", "no_separator"])

    assert result.exit_code != 0
    mock_run_create.assert_not_called()


@patch("plonecli.cli._is_interactive", return_value=False)
@patch("plonecli.cli.find_project_root")
@patch("plonecli.cli.load_config")
@patch("plonecli.cli.run_create")
@patch("plonecli.cli.dirty_files", return_value=(["src/foo.py"], []))
def test_setup_dirty_repo_fails_in_non_interactive_mode(
    mock_dirty,
    mock_run_create,
    mock_config,
    mock_project,
    mock_tty,
    runner,
    tmp_path,
):
    mock_config.return_value = MagicMock(templates_dir=str(tmp_path))
    mock_project.return_value = project_at(tmp_path)

    result = runner.invoke(cli, ["setup", "--defaults"])

    assert result.exit_code != 0
    assert "--allow-dirty" in result.output
    mock_run_create.assert_not_called()


@patch("plonecli.cli._is_interactive", return_value=False)
@patch("plonecli.cli.find_project_root")
@patch("plonecli.cli.load_config")
@patch("plonecli.cli.run_create")
@patch("plonecli.cli.dirty_files", return_value=(["src/foo.py"], []))
def test_setup_allow_dirty_proceeds(
    mock_dirty,
    mock_run_create,
    mock_config,
    mock_project,
    mock_tty,
    runner,
    tmp_path,
):
    mock_config.return_value = MagicMock(templates_dir=str(tmp_path))
    mock_project.return_value = project_at(tmp_path)

    result = runner.invoke(cli, ["setup", "--defaults", "--allow-dirty"])

    assert result.exit_code == 0, result.output
    mock_run_create.assert_called_once()

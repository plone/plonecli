"""Tests for plonecli.templates module."""

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click import ClickException

from plonecli.config import PlonecliConfig
from plonecli.templates import (
    ensure_templates_cloned,
    get_template_path,
    get_templates_info,
    run_add,
    run_create,
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
    ensure_templates_cloned(config)

    mock_run.assert_called_once()
    call_args = mock_run.call_args[0][0]
    assert "git" in call_args
    assert "clone" in call_args
    assert "--depth" in call_args
    assert "https://example.com/repo" in call_args


@patch("plonecli.templates.subprocess.run")
def test_update_templates_clone_up_to_date(mock_run, tmp_path):
    templates_dir = tmp_path / "templates"
    templates_dir.mkdir()
    (templates_dir / ".git").mkdir()

    sha = "abc1234abc1234abc1234abc1234abc1234abc1"
    mock_run.side_effect = [
        MagicMock(returncode=0, stdout="", stderr=""),  # fetch
        MagicMock(returncode=0, stdout=sha + "\n", stderr=""),  # rev-parse HEAD
        MagicMock(returncode=0, stdout=sha + "\n", stderr=""),  # rev-parse origin
    ]

    config = PlonecliConfig(templates_dir=str(templates_dir))
    msg = update_templates_clone(config)

    assert "up to date" in msg.lower()
    assert mock_run.call_count == 3


@patch("plonecli.templates.subprocess.run")
def test_update_templates_clone_resets_on_divergence(mock_run, tmp_path):
    """When local and origin diverge, hard-reset to origin instead of failing."""
    templates_dir = tmp_path / "templates"
    templates_dir.mkdir()
    (templates_dir / ".git").mkdir()

    before = "951b15c951b15c951b15c951b15c951b15c951b1"
    after = "9e89e5b9e89e5b9e89e5b9e89e5b9e89e5b9e89e"
    mock_run.side_effect = [
        MagicMock(returncode=0, stdout="", stderr=""),  # fetch
        MagicMock(returncode=0, stdout=before + "\n", stderr=""),  # HEAD
        MagicMock(returncode=0, stdout=after + "\n", stderr=""),  # origin/branch
        MagicMock(returncode=0, stdout="", stderr=""),  # reset --hard
    ]

    config = PlonecliConfig(templates_dir=str(templates_dir), repo_branch="main")
    msg = update_templates_clone(config)

    assert "updated" in msg.lower()
    assert "951b15c" in msg
    assert "9e89e5b" in msg
    reset_call = mock_run.call_args_list[3][0][0]
    assert reset_call == ["git", "reset", "--hard", "origin/main"]


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


@patch("plonecli.templates.run_copy")
def test_run_create_overwrite_default_false(mock_run_copy, tmp_path):
    """run_create does not overwrite by default."""
    (tmp_path / ".git").mkdir()
    (tmp_path / "backend_addon").mkdir()
    config = PlonecliConfig(templates_dir=str(tmp_path))
    run_create("backend_addon", "out", config, defaults=True, git_commit=False)
    assert mock_run_copy.call_args.kwargs["overwrite"] is False


@patch("plonecli.templates.run_copy")
def test_run_create_overwrite_forwarded(mock_run_copy, tmp_path):
    """overwrite=True is forwarded to copier (layering onto existing files)."""
    (tmp_path / ".git").mkdir()
    (tmp_path / "zope-setup").mkdir()
    config = PlonecliConfig(templates_dir=str(tmp_path))
    run_create(
        "zope-setup",
        "out",
        config,
        defaults=True,
        git_commit=False,
        overwrite=True,
    )
    assert mock_run_copy.call_args.kwargs["overwrite"] is True


VIEW_COPIER_YML = """\
_subdirectory: template
_answers_file: .copier-answers.view.yml
_plonecli:
  type: sub
  parent: backend_addon
  commit_message: "Add view {view_name}"
view_name:
  type: str
  default: myview
  validator: "{% if view_name == 'bad' %}bad is not allowed{% endif %}"
"""


@pytest.fixture
def view_setup(tmp_path):
    """A tiny real subtemplate plus a project dir to render it into."""
    from tests.helpers import project_at

    templates = tmp_path / "templates"
    (templates / ".git").mkdir(parents=True)
    view = templates / "view"
    (view / "template/views").mkdir(parents=True)
    (view / "copier.yml").write_text(VIEW_COPIER_YML)
    (view / "template/shared.txt").write_text("shared\n")
    (view / "template/{{ _copier_conf.answers_file }}.jinja").write_text(
        "{{ _copier_answers|to_nice_yaml }}"
    )
    (view / "template/views/{{view_name}}.py.jinja").write_text("# {{ view_name }}\n")
    project = tmp_path / "project"
    project.mkdir()
    return PlonecliConfig(templates_dir=str(templates)), project_at(project), project


def _add_view(view_setup, **kwargs):
    config, project, _ = view_setup
    kwargs.setdefault("defaults", True)
    kwargs.setdefault("git_commit", False)
    return run_add("view", project, config, **kwargs)


def test_run_add_fail_mode_renders_without_conflicts(view_setup):
    _add_view(view_setup, on_conflict="fail")
    root = view_setup[2]
    assert (root / "views/myview.py").read_text() == "# myview\n"
    assert (root / "shared.txt").exists()


def test_run_add_fail_mode_reports_conflicts_before_writing(view_setup):
    root = view_setup[2]
    (root / "shared.txt").write_text("customised\n")

    with pytest.raises(ClickException) as exc:
        _add_view(view_setup, on_conflict="fail")

    message = exc.value.format_message()
    assert "shared.txt" in message
    assert "--overwrite" in message
    assert "--skip-existing" in message
    assert "\n" not in message
    assert not (root / "views").exists()
    assert (root / "shared.txt").read_text() == "customised\n"


def test_run_add_identical_files_are_no_conflict(view_setup):
    _add_view(view_setup, on_conflict="fail")
    _add_view(view_setup, on_conflict="fail", data={"view_name": "other"})
    assert (view_setup[2] / "views/other.py").exists()


def test_run_add_skip_existing_keeps_files(view_setup):
    root = view_setup[2]
    (root / "shared.txt").write_text("customised\n")

    _add_view(view_setup, on_conflict="skip")

    assert (root / "shared.txt").read_text() == "customised\n"
    assert (root / "views/myview.py").exists()
    assert (root / ".copier-answers.view.yml").exists()


def test_run_add_overwrite_replaces_files(view_setup):
    root = view_setup[2]
    (root / "shared.txt").write_text("customised\n")

    _add_view(view_setup, on_conflict="overwrite")

    assert (root / "shared.txt").read_text() == "shared\n"


def test_run_add_validation_error_is_one_line(view_setup):
    with pytest.raises(ClickException) as exc:
        _add_view(view_setup, on_conflict="fail", data={"view_name": "bad"})

    assert exc.value.format_message() == (
        "Validation error for question 'view_name': bad is not allowed"
    )
    assert not (view_setup[2] / "views").exists()


def test_run_add_commit_message_from_template(view_setup):
    root = view_setup[2]
    subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True)

    message = _add_view(view_setup, on_conflict="fail", git_commit=True)

    assert message == "Add view myview"


def test_run_add_commit_message_falls_back_on_unknown_key(view_setup):
    config, _, root = view_setup
    copier_yml = Path(config.templates_dir) / "view/copier.yml"
    copier_yml.write_text(VIEW_COPIER_YML.replace("{view_name}", "{missing}"))
    subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True)

    message = _add_view(view_setup, on_conflict="fail", git_commit=True)

    assert message == "Add view subtemplate"

"""CLI-level tests for ``plonecli update`` and the update banner."""

import json
from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest

from plonecli.cli import cli


@pytest.fixture
def config(tmp_path):
    return MagicMock(templates_dir=str(tmp_path))


@patch("plonecli.cli.find_project_root", return_value=None)
@patch("plonecli.cli.load_config")
@patch("plonecli.cli.get_templates_info", return_value="abc1234 2026-07-26")
@patch("plonecli.cli.update_templates_clone", return_value="Templates updated: a → b")
@patch("plonecli.cli.ensure_templates_cloned")
@patch("plonecli.updater.check_for_updates", return_value=None)
def test_update_reports_template_update(
    mock_check,
    mock_ensure,
    mock_update,
    mock_info,
    mock_config,
    mock_project,
    runner,
    config,
):
    mock_config.return_value = config

    result = runner.invoke(cli, ["update"])

    assert result.exit_code == 0, result.output
    assert "Templates updated: a → b" in result.output
    assert "up to date" in result.output
    assert "abc1234" in result.output
    # ``update`` forces a fresh PyPI check rather than reusing the 24h cache.
    assert any(call.kwargs.get("force") for call in mock_check.call_args_list)


@patch("plonecli.cli.find_project_root", return_value=None)
@patch("plonecli.cli.load_config")
@patch("plonecli.cli.get_templates_info", return_value="abc1234 2026-07-26")
@patch("plonecli.cli.update_templates_clone")
@patch("plonecli.cli.ensure_templates_cloned")
@patch("plonecli.updater.check_for_updates", return_value=None)
def test_update_reports_template_failure_without_aborting(
    mock_check,
    mock_ensure,
    mock_update,
    mock_info,
    mock_config,
    mock_project,
    runner,
    config,
):
    """A failed template fetch must not hide the plonecli version check."""
    mock_config.return_value = config
    mock_update.side_effect = RuntimeError("network unreachable")

    result = runner.invoke(cli, ["update"])

    assert result.exit_code == 0, result.output
    assert "Failed to update templates: network unreachable" in result.output
    assert "up to date" in result.output


@patch("plonecli.cli.find_project_root", return_value=None)
@patch("plonecli.cli.load_config")
@patch("plonecli.cli.get_templates_info", return_value="abc1234 2026-07-26")
@patch(
    "plonecli.cli.update_templates_clone", return_value="Templates already up to date."
)
@patch("plonecli.cli.ensure_templates_cloned")
@patch("plonecli.updater.check_for_updates", return_value="7.0.0b14")
@patch("plonecli.cli.importlib.metadata.version", return_value="7.0.0b13")
def test_update_reports_new_plonecli_version(
    mock_version,
    mock_check,
    mock_ensure,
    mock_update,
    mock_info,
    mock_config,
    mock_project,
    runner,
    config,
):
    mock_config.return_value = config

    result = runner.invoke(cli, ["update"])

    assert result.exit_code == 0, result.output
    assert "New version available: 7.0.0b14" in result.output
    assert "current: 7.0.0b13" in result.output
    assert "uv tool upgrade plonecli" in result.output


@patch("plonecli.cli.find_project_root", return_value=None)
@patch("plonecli.cli.load_config")
@patch("plonecli.cli.get_templates_info", return_value="abc1234 2026-07-26")
@patch(
    "plonecli.cli.update_templates_clone", return_value="Templates already up to date."
)
@patch("plonecli.cli.ensure_templates_cloned")
@patch("plonecli.updater.check_for_updates")
def test_update_reports_version_check_failure(
    mock_check,
    mock_ensure,
    mock_update,
    mock_info,
    mock_config,
    mock_project,
    runner,
    config,
):
    mock_config.return_value = config
    mock_check.side_effect = OSError("no route to host")

    result = runner.invoke(cli, ["update"])

    assert result.exit_code == 0, result.output
    assert "Could not check for updates: no route to host" in result.output
    # The templates info is still reported.
    assert "abc1234" in result.output


@patch("plonecli.cli.find_project_root", return_value=None)
@patch("plonecli.cli.load_config")
@patch("plonecli.updater.check_for_updates", return_value="7.0.0b14")
def test_banner_shown_when_a_newer_version_exists(
    mock_check, mock_config, mock_project, runner, config
):
    """Regression: the notifier compared release segments only, so it never
    fired while plonecli shipped betas."""
    mock_config.return_value = config

    result = runner.invoke(cli, [])

    assert "A new version of plonecli is available: 7.0.0b14" in result.output
    assert "uv tool upgrade plonecli" in result.output


@patch("plonecli.cli.find_project_root", return_value=None)
@patch("plonecli.cli.load_config")
@patch("plonecli.updater.check_for_updates", return_value=None)
def test_banner_silent_when_current(
    mock_check, mock_config, mock_project, runner, config
):
    mock_config.return_value = config

    result = runner.invoke(cli, [])

    assert "new version of plonecli" not in result.output


@patch("plonecli.cli.find_project_root", return_value=None)
@patch("plonecli.cli.load_config")
@patch("plonecli.updater._get_current_version", return_value="7.0.0b13")
def test_banner_renders_from_a_pypi_response(
    mock_current, mock_config, mock_project, runner, config, tmp_path, monkeypatch
):
    """The whole notifier chain, from the PyPI payload to the banner.

    Regression: the version comparison stripped pre-release suffixes, so this
    path silently produced nothing for every beta release plonecli shipped.
    """
    mock_config.return_value = config
    monkeypatch.setattr(
        "plonecli.updater.UPDATE_CACHE_FILE", tmp_path / ".update_cache.json"
    )
    monkeypatch.setattr("plonecli.updater.CONFIG_DIR", tmp_path)
    payload = json.dumps({"info": {"version": "7.0.0b14"}}).encode("utf-8")
    monkeypatch.setattr("plonecli.updater.urlopen", lambda *a, **k: BytesIO(payload))

    result = runner.invoke(cli, [])

    assert "A new version of plonecli is available: 7.0.0b14" in result.output


@patch("plonecli.cli.find_project_root", return_value=None)
@patch("plonecli.cli.load_config")
@patch("plonecli.updater._get_current_version", return_value="7.0.0b14")
def test_no_banner_when_pypi_reports_the_installed_version(
    mock_current, mock_config, mock_project, runner, config, tmp_path, monkeypatch
):
    mock_config.return_value = config
    monkeypatch.setattr(
        "plonecli.updater.UPDATE_CACHE_FILE", tmp_path / ".update_cache.json"
    )
    monkeypatch.setattr("plonecli.updater.CONFIG_DIR", tmp_path)
    payload = json.dumps({"info": {"version": "7.0.0b14"}}).encode("utf-8")
    monkeypatch.setattr("plonecli.updater.urlopen", lambda *a, **k: BytesIO(payload))

    result = runner.invoke(cli, [])

    assert "new version of plonecli" not in result.output


@patch("plonecli.cli.find_project_root", return_value=None)
@patch("plonecli.cli.load_config")
@patch("plonecli.updater.check_for_updates")
def test_banner_never_breaks_the_cli(
    mock_check, mock_config, mock_project, runner, config
):
    """An update check failure must stay invisible on a normal invocation."""
    mock_config.return_value = config
    mock_check.side_effect = OSError("offline")

    result = runner.invoke(cli, ["--help"])

    assert result.exit_code == 0, result.output

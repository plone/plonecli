"""CLI-level tests for the ``plonecli config`` command."""

from unittest.mock import patch

import pytest

from plonecli.cli import cli
from plonecli.config import PlonecliConfig, load_config


@pytest.fixture
def isolated_config(tmp_path, monkeypatch):
    """Point the config module at a temp home and return the config file path."""
    home = tmp_path / "home"
    home.mkdir()
    config_dir = home / ".plonecli"
    config_file = config_dir / "config.toml"
    monkeypatch.setattr("plonecli.config.CONFIG_DIR", config_dir)
    monkeypatch.setattr("plonecli.config.CONFIG_FILE", config_file)
    monkeypatch.setattr("plonecli.config.Path.home", lambda: home)
    monkeypatch.setenv("HOME", str(home))
    for var in (
        "PLONECLI_TEMPLATES_REPO_URL",
        "PLONECLI_TEMPLATES_BRANCH",
        "PLONECLI_TEMPLATES_DIR",
    ):
        monkeypatch.delenv(var, raising=False)
    return config_file


# In prompt order, so the values can be fed to the command as one input stream.
ANSWERS = {
    "author_name": "Jane Doe",
    "author_email": "jane@example.com",
    "github_user": "janedoe",
    "plone_version": "6.1.1",
    "repo_url": "https://github.com/plone/copier-templates",
    "repo_branch": "main",
}


def _input(**overrides):
    """The scripted prompt answers, with named ones replaced."""
    return "\n".join((ANSWERS | overrides).values()) + "\n"


def _accept_defaults(**overrides):
    """Press Enter at every prompt, except where an answer is given."""
    return "\n".join((dict.fromkeys(ANSWERS, "") | overrides).values()) + "\n"


@patch("plonecli.cli.find_project_root", return_value=None)
@patch("plonecli.plone_versions.get_latest_stable_version", return_value="6.1.1")
def test_config_prompts_and_saves(mock_latest, mock_project, runner, isolated_config):
    result = runner.invoke(cli, ["config"], input=_input())

    assert result.exit_code == 0, result.output
    assert str(isolated_config) in result.output
    saved = load_config()
    assert saved.author_name == "Jane Doe"
    assert saved.author_email == "jane@example.com"
    assert saved.github_user == "janedoe"
    assert saved.plone_version == "6.1.1"


@patch("plonecli.cli.find_project_root", return_value=None)
@patch("plonecli.plone_versions.get_latest_stable_version", return_value="6.1.1")
def test_config_suggests_latest_plone_version(
    mock_latest, mock_project, runner, isolated_config
):
    """An empty answer takes the suggested latest stable release."""
    result = runner.invoke(cli, ["config"], input=_input(plone_version=""))

    assert result.exit_code == 0, result.output
    assert load_config().plone_version == "6.1.1"


@patch("plonecli.cli.find_project_root", return_value=None)
@patch("plonecli.plone_versions.get_latest_stable_version", return_value="6.1.1")
def test_config_round_trips_hostile_author_name(
    mock_latest, mock_project, runner, isolated_config
):
    """A quote in the author name must not corrupt the saved config.

    Regression: the saved file became unparseable, so every later plonecli
    invocation - including a second ``plonecli config`` - failed.
    """
    hostile = 'Ann "The Hammer" O\'Neill'

    result = runner.invoke(cli, ["config"], input=_input(author_name=hostile))

    assert result.exit_code == 0, result.output
    assert load_config().author_name == hostile

    # And the config command can be run again on top of it.
    again = runner.invoke(cli, ["config"], input=_input())
    assert again.exit_code == 0, again.output


@patch("plonecli.cli.find_project_root", return_value=None)
@patch("plonecli.plone_versions.get_latest_stable_version", return_value="6.1.1")
def test_config_offers_mrbob_migration(
    mock_latest, mock_project, runner, isolated_config
):
    home = isolated_config.parent.parent
    (home / ".mrbob").write_text(
        "[variables]\n"
        "author.name = Bob User\n"
        "author.email = bob@example.com\n"
        "author.github.user = bobuser\n"
        "\n[defaults]\n"
        "plone.version = 6.0.11\n"
    )

    # Accept the import, then accept every prefilled default.
    result = runner.invoke(cli, ["config"], input="y\n" + _accept_defaults())

    assert result.exit_code == 0, result.output
    assert "~/.mrbob" in result.output
    saved = load_config()
    assert saved.author_name == "Bob User"
    assert saved.author_email == "bob@example.com"
    assert saved.github_user == "bobuser"
    assert saved.plone_version == "6.0.11"


@patch("plonecli.cli.find_project_root", return_value=None)
@patch("plonecli.plone_versions.get_latest_stable_version", return_value="6.1.1")
def test_config_declining_mrbob_migration_keeps_defaults(
    mock_latest, mock_project, runner, isolated_config
):
    home = isolated_config.parent.parent
    (home / ".mrbob").write_text("[variables]\nauthor.name = Bob User\n")

    result = runner.invoke(cli, ["config"], input="n\n" + _accept_defaults())

    assert result.exit_code == 0, result.output
    assert load_config().author_name == PlonecliConfig().author_name


@patch("plonecli.cli.find_project_root", return_value=None)
@patch("plonecli.plone_versions.get_latest_stable_version", return_value="6.1.1")
def test_config_no_mrbob_offer_once_configured(
    mock_latest, mock_project, runner, isolated_config
):
    """The migration offer is a first-run thing only."""
    home = isolated_config.parent.parent
    (home / ".mrbob").write_text("[variables]\nauthor.name = Bob User\n")
    first = runner.invoke(cli, ["config"], input="n\n" + _input())
    assert first.exit_code == 0, first.output

    result = runner.invoke(cli, ["config"], input=_accept_defaults())

    assert result.exit_code == 0, result.output
    assert "~/.mrbob" not in result.output
    assert load_config().author_name == "Jane Doe"


@pytest.mark.parametrize("args", [["-V"], ["config"]])
@patch("plonecli.cli.find_project_root", return_value=None)
def test_broken_config_reports_the_path_and_the_recovery(
    mock_project, runner, isolated_config, args
):
    """An unreadable config must explain itself, not raise a parse error.

    It is loaded up front for every command, so ``plonecli config`` cannot
    rewrite it either - hence the ``rm`` in the message.
    """
    isolated_config.parent.mkdir(parents=True, exist_ok=True)
    isolated_config.write_text('[author]\nname = "unterminated\n')

    result = runner.invoke(cli, args)

    assert result.exit_code != 0
    assert str(isolated_config) in result.output
    assert "rm " in result.output


@patch("plonecli.cli.find_project_root", return_value=None)
@patch("plonecli.plone_versions.get_latest_stable_version", return_value="6.1.1")
def test_config_keeps_existing_values_as_defaults(
    mock_latest, mock_project, runner, isolated_config
):
    runner.invoke(cli, ["config"], input=_input())

    # Change only the email; empty answers keep each stored value.
    result = runner.invoke(
        cli, ["config"], input=_accept_defaults(author_email="new@example.com")
    )

    assert result.exit_code == 0, result.output
    saved = load_config()
    assert saved.author_email == "new@example.com"
    assert saved.author_name == "Jane Doe"
    assert saved.github_user == "janedoe"

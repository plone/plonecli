"""Tests for plonecli.config module."""

from pathlib import Path

from plonecli.config import (
    PlonecliConfig,
    load_config,
    migrate_from_mrbob,
    save_config,
)


def test_default_config():
    config = PlonecliConfig()
    assert config.author_name == "Plone Developer"
    assert config.author_email == "dev@plone.org"
    assert config.github_user == ""
    assert config.plone_version == ""
    assert "plone/copier-templates" in config.repo_url
    assert config.repo_branch == "main"
    assert config.auto_commit is True


def test_auto_commit_load_save_roundtrip(tmp_path, monkeypatch):
    config_dir = tmp_path / ".plonecli"
    config_file = config_dir / "config.toml"
    monkeypatch.setattr("plonecli.config.CONFIG_DIR", config_dir)
    monkeypatch.setattr("plonecli.config.CONFIG_FILE", config_file)

    save_config(PlonecliConfig(auto_commit=False))
    assert "auto_commit = false" in config_file.read_text()
    assert load_config().auto_commit is False


def test_load_config_missing_file(tmp_path, monkeypatch):
    monkeypatch.setattr("plonecli.config.CONFIG_FILE", tmp_path / "nonexistent.toml")
    config = load_config()
    assert config.author_name == "Plone Developer"


def test_load_config(tmp_path, monkeypatch):
    config_file = tmp_path / "config.toml"
    config_file.write_text("""\
[author]
name = "Test User"
email = "test@example.com"
github_user = "testuser"

[defaults]
plone_version = "6.1.1"

[templates]
repo_url = "https://github.com/test/repo"
branch = "develop"
local_path = "~/my-templates"
""")
    monkeypatch.setattr("plonecli.config.CONFIG_FILE", config_file)

    config = load_config()
    assert config.author_name == "Test User"
    assert config.author_email == "test@example.com"
    assert config.github_user == "testuser"
    assert config.plone_version == "6.1.1"
    assert config.repo_url == "https://github.com/test/repo"
    assert config.repo_branch == "develop"


def test_save_config(tmp_path, monkeypatch):
    config_dir = tmp_path / ".plonecli"
    config_file = config_dir / "config.toml"
    monkeypatch.setattr("plonecli.config.CONFIG_DIR", config_dir)
    monkeypatch.setattr("plonecli.config.CONFIG_FILE", config_file)

    config = PlonecliConfig(
        author_name="Jane Doe",
        author_email="jane@example.com",
        github_user="janedoe",
        plone_version="6.0.13",
    )
    save_config(config)

    assert config_file.exists()
    content = config_file.read_text()
    assert 'name = "Jane Doe"' in content
    assert 'email = "jane@example.com"' in content
    assert 'plone_version = "6.0.13"' in content


def test_save_collapses_home_in_templates_path(tmp_path, monkeypatch):
    """The default templates_dir is stored home-relative, not as an absolute path.

    Regression: an absolute ``/home/<user>/...`` baked into config.toml broke
    when the same config was read under a different ``$HOME`` (host vs.
    devcontainer).
    """
    home = tmp_path / "home"
    monkeypatch.setenv("HOME", str(home))
    config_dir = home / ".plonecli"
    config_file = config_dir / "config.toml"
    monkeypatch.setattr("plonecli.config.CONFIG_DIR", config_dir)
    monkeypatch.setattr("plonecli.config.CONFIG_FILE", config_file)

    save_config(PlonecliConfig(templates_dir=str(home / ".copier-templates" / "x")))

    content = config_file.read_text()
    assert 'local_path = "~/.copier-templates/x"' in content
    assert str(home) not in content


def test_save_keeps_paths_outside_home_absolute(tmp_path, monkeypatch):
    home = tmp_path / "home"
    monkeypatch.setenv("HOME", str(home))
    config_dir = home / ".plonecli"
    config_file = config_dir / "config.toml"
    monkeypatch.setattr("plonecli.config.CONFIG_DIR", config_dir)
    monkeypatch.setattr("plonecli.config.CONFIG_FILE", config_file)

    save_config(PlonecliConfig(templates_dir="/opt/templates"))

    assert 'local_path = "/opt/templates"' in config_file.read_text()


def test_templates_path_reloads_under_different_home(tmp_path, monkeypatch):
    """A config saved under one $HOME expands correctly under another."""
    config_dir = tmp_path / ".plonecli"
    config_file = config_dir / "config.toml"
    monkeypatch.setattr("plonecli.config.CONFIG_DIR", config_dir)
    monkeypatch.setattr("plonecli.config.CONFIG_FILE", config_file)

    home_a = tmp_path / "home_a"
    monkeypatch.setenv("HOME", str(home_a))
    save_config(PlonecliConfig(templates_dir=str(home_a / ".copier-templates" / "x")))

    home_b = tmp_path / "home_b"
    monkeypatch.setenv("HOME", str(home_b))
    loaded = load_config()
    assert loaded.templates_dir == str(home_b / ".copier-templates" / "x")


def test_save_and_reload(tmp_path, monkeypatch):
    config_dir = tmp_path / ".plonecli"
    config_file = config_dir / "config.toml"
    monkeypatch.setattr("plonecli.config.CONFIG_DIR", config_dir)
    monkeypatch.setattr("plonecli.config.CONFIG_FILE", config_file)

    original = PlonecliConfig(
        author_name="Round Trip",
        author_email="rt@example.com",
        plone_version="6.1.0",
    )
    save_config(original)
    loaded = load_config()

    assert loaded.author_name == original.author_name
    assert loaded.author_email == original.author_email
    assert loaded.plone_version == original.plone_version


def test_migrate_from_mrbob(tmp_path, monkeypatch):
    mrbob_file = tmp_path / ".mrbob"
    mrbob_file.write_text("""\
[mr.bob]
verbose = False

[variables]
author.name = Bob User
author.email = bob@example.com
author.github.user = bobuser

[defaults]
plone.version = 6.0.11
""")
    monkeypatch.setattr("plonecli.config.Path.home", lambda: tmp_path)

    config = migrate_from_mrbob()
    assert config is not None
    assert config.author_name == "Bob User"
    assert config.author_email == "bob@example.com"
    assert config.github_user == "bobuser"
    assert config.plone_version == "6.0.11"


def test_migrate_from_mrbob_missing(tmp_path, monkeypatch):
    monkeypatch.setattr("plonecli.config.Path.home", lambda: tmp_path)
    config = migrate_from_mrbob()
    assert config is None


def test_env_var_overrides(tmp_path, monkeypatch):
    """Environment variables override config file values."""
    config_file = tmp_path / "config.toml"
    config_file.write_text("""\
[templates]
repo_url = "https://github.com/original/repo"
branch = "main"
local_path = "/original/path"
""")
    monkeypatch.setattr("plonecli.config.CONFIG_FILE", config_file)
    monkeypatch.setenv("PLONECLI_TEMPLATES_REPO_URL", "https://github.com/override/repo")
    monkeypatch.setenv("PLONECLI_TEMPLATES_BRANCH", "develop")
    monkeypatch.setenv("PLONECLI_TEMPLATES_DIR", "/override/path")

    config = load_config()
    assert config.repo_url == "https://github.com/override/repo"
    assert config.repo_branch == "develop"
    assert config.templates_dir == "/override/path"


def test_env_var_without_config_file(tmp_path, monkeypatch):
    """Environment variables work even without a config file."""
    monkeypatch.setattr("plonecli.config.CONFIG_FILE", tmp_path / "nonexistent.toml")
    monkeypatch.setenv("PLONECLI_TEMPLATES_REPO_URL", "https://github.com/custom/repo")

    config = load_config()
    assert config.repo_url == "https://github.com/custom/repo"

"""Global plonecli configuration management."""

from __future__ import annotations

import configparser
import os
import tomllib
from dataclasses import dataclass
from pathlib import Path


CONFIG_DIR = Path.home() / ".plonecli"
CONFIG_FILE = CONFIG_DIR / "config.toml"
TEMPLATES_DIR = Path.home() / ".copier-templates" / "plone-copier-templates"
DEFAULT_REPO_URL = "https://github.com/derico-de/copier-templates"
DEFAULT_BRANCH = "main"

# Environment variable overrides
ENV_REPO_URL = "PLONECLI_TEMPLATES_REPO_URL"
ENV_REPO_BRANCH = "PLONECLI_TEMPLATES_BRANCH"
ENV_TEMPLATES_DIR = "PLONECLI_TEMPLATES_DIR"


@dataclass
class PlonecliConfig:
    author_name: str = "Plone Developer"
    author_email: str = "dev@plone.org"
    github_user: str = ""
    plone_version: str = ""
    repo_url: str = DEFAULT_REPO_URL
    repo_branch: str = DEFAULT_BRANCH
    templates_dir: str = str(TEMPLATES_DIR)


def load_config() -> PlonecliConfig:
    """Load config from ~/.plonecli/config.toml.

    Environment variables take precedence over config file values:
    - PLONECLI_TEMPLATES_REPO_URL: Override the templates repo URL
    - PLONECLI_TEMPLATES_BRANCH: Override the templates branch
    - PLONECLI_TEMPLATES_DIR: Override the local templates directory

    Returns a PlonecliConfig with defaults for any missing values.
    """
    config = PlonecliConfig()
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "rb") as f:
            data = tomllib.load(f)

        author = data.get("author", {})
        defaults = data.get("defaults", {})
        templates = data.get("templates", {})

        config.author_name = author.get("name", config.author_name)
        config.author_email = author.get("email", config.author_email)
        config.github_user = author.get("github_user", config.github_user)
        config.plone_version = defaults.get("plone_version", config.plone_version)
        config.repo_url = templates.get("repo_url", config.repo_url)
        config.repo_branch = templates.get("branch", config.repo_branch)
        config.templates_dir = templates.get("local_path", config.templates_dir)

    # Environment variables override config file
    if os.environ.get(ENV_REPO_URL):
        config.repo_url = os.environ[ENV_REPO_URL]
    if os.environ.get(ENV_REPO_BRANCH):
        config.repo_branch = os.environ[ENV_REPO_BRANCH]
    if os.environ.get(ENV_TEMPLATES_DIR):
        config.templates_dir = os.environ[ENV_TEMPLATES_DIR]

    # Expand ~ in templates_dir
    config.templates_dir = str(Path(config.templates_dir).expanduser())

    return config


def save_config(config: PlonecliConfig) -> None:
    """Save config to ~/.plonecli/config.toml."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    content = f"""\
[author]
name = "{config.author_name}"
email = "{config.author_email}"
github_user = "{config.github_user}"

[defaults]
plone_version = "{config.plone_version}"

[templates]
repo_url = "{config.repo_url}"
branch = "{config.repo_branch}"
local_path = "{config.templates_dir}"
"""
    CONFIG_FILE.write_text(content)


def migrate_from_mrbob() -> PlonecliConfig | None:
    """Attempt to read settings from ~/.mrbob and return a config.

    Returns None if ~/.mrbob doesn't exist or can't be parsed.
    """
    mrbob_file = Path.home() / ".mrbob"
    if not mrbob_file.exists():
        return None

    parser = configparser.ConfigParser()
    try:
        parser.read(str(mrbob_file))
    except configparser.Error:
        return None

    config = PlonecliConfig()
    if parser.has_section("variables"):
        variables = dict(parser.items("variables"))
        config.author_name = variables.get("author.name", config.author_name)
        config.author_email = variables.get("author.email", config.author_email)
        config.github_user = variables.get(
            "author.github.user", config.github_user
        )

    if parser.has_section("defaults"):
        defaults = dict(parser.items("defaults"))
        config.plone_version = defaults.get(
            "plone.version", config.plone_version
        )

    return config

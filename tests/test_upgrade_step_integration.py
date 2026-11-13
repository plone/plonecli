"""``plonecli add upgrade_step`` against the real templates, the way agents run it.

Needs a copier-templates checkout (see ``PLONECLI_TEMPLATES_DIR``); marked
``integration``.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from plonecli.cli import cli
from plonecli.config import PlonecliConfig


def _templates_dir() -> Path:
    env_dir = os.environ.get("PLONECLI_TEMPLATES_DIR")
    candidates = [env_dir] if env_dir else []
    candidates += [
        PlonecliConfig().templates_dir,
        "/home/node/develop/plone/src/copier-templates",
        "/home/node/.copier-templates/plone-copier-templates",
    ]
    for c in candidates:
        if c and (Path(c) / "upgrade_step" / "copier.yml").exists():
            return Path(c)
    pytest.skip("No copier-templates checkout with upgrade_step available")


def _git(project, *args):
    return subprocess.run(
        ["git", *args], cwd=project, capture_output=True, text=True, check=True
    ).stdout.strip()


@pytest.fixture
def plonecli(tmp_path, monkeypatch):
    config = PlonecliConfig(
        templates_dir=str(_templates_dir()),
        author_name="Plone Developer",
        author_email="dev@plone.org",
    )
    runner = CliRunner()
    project = tmp_path / "collective.steps"

    def invoke(*args):
        with (
            patch("plonecli.cli.load_config", return_value=config),
            patch("plonecli.cli.ensure_templates_cloned"),
            patch("plonecli.templates.ensure_templates_cloned"),
        ):
            return runner.invoke(cli, list(args))

    monkeypatch.chdir(tmp_path)
    result = invoke("create", "backend_addon", project.name, "--defaults")
    assert result.exit_code == 0, result.output
    monkeypatch.chdir(project)
    return invoke, project


def _add_step(invoke, *data):
    args = ["add", "upgrade_step", "--defaults"]
    for pair in data:
        args += ["-d", pair]
    return invoke(*args)


@pytest.mark.integration
def test_repeated_steps_commit_with_their_title(plonecli):
    invoke, project = plonecli

    first = _add_step(
        invoke,
        "upgrade_step_title=Add settings",
        "upgrade_step_import_steps=[plone.app.registry]",
    )
    second = _add_step(invoke, "upgrade_step_title=Clean up")

    assert first.exit_code == 0, first.output
    assert second.exit_code == 0, second.output
    assert _git(project, "log", "--format=%s", "-2").splitlines() == [
        "Add upgrade step 1002: Clean up",
        "Add upgrade step 1001: Add settings",
    ]
    assert _git(project, "status", "--porcelain") == ""
    upgrades = project / "src/collective/steps/upgrades"
    assert (upgrades / "1001").is_dir()
    assert not (upgrades / "1002").exists()


@pytest.mark.integration
def test_existing_destination_fails_cleanly(plonecli):
    invoke, project = plonecli
    assert _add_step(invoke, "upgrade_step_title=Add settings").exit_code == 0
    head = _git(project, "rev-parse", "HEAD")

    result = _add_step(
        invoke,
        "upgrade_step_title=Again",
        "source_version=1000",
        "destination_version=1001",
    )

    assert result.exit_code != 0
    assert "upgrades/v1001.py already exists" in result.output
    assert "Traceback" not in result.output
    assert _git(project, "rev-parse", "HEAD") == head
    assert _git(project, "status", "--porcelain") == ""


@pytest.mark.integration
def test_add_to_work_in_progress_stays_uncommitted(plonecli):
    invoke, project = plonecli
    profile = project / "src/collective/steps/profiles/default/registry.xml"
    profile.parent.mkdir(parents=True, exist_ok=True)
    profile.write_text("<registry />\n")
    head = _git(project, "rev-parse", "HEAD")

    result = invoke(
        "add",
        "upgrade_step",
        "--defaults",
        "--allow-dirty",
        "-d",
        "upgrade_step_title=Register settings",
    )

    assert result.exit_code == 0, result.output
    assert "left uncommitted" in result.output
    assert _git(project, "rev-parse", "HEAD") == head
    assert "v1001.py" in _git(project, "status", "--porcelain", "-uall")

"""End-to-end test for the theme_barceloneta subtemplate.

This test generates a fresh backend_addon, adds the theme_barceloneta
subtemplate on top, then runs the generated package's own pytest suite
(which includes a theme verification test shipped with the template) to
confirm the theme installs and is active inside a real Plone instance.

It is slow (builds Plone via ``uv sync``) and requires network access on
first run, so it is marked ``integration`` and deselected by default.
Run explicitly with::

    uv run pytest -m integration tests/test_theme_barceloneta_integration.py
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

from plonecli.config import PlonecliConfig
from plonecli.project import find_project_root
from plonecli.templates import run_add, run_create


DEV_TEMPLATES_DIR = Path("/home/node/develop/plone/src/copier-templates")
FALLBACK_TEMPLATES_DIR = Path(
    "/home/node/.copier-templates/plone-copier-templates"
)


def _templates_dir() -> Path:
    if DEV_TEMPLATES_DIR.exists():
        return DEV_TEMPLATES_DIR
    if FALLBACK_TEMPLATES_DIR.exists():
        return FALLBACK_TEMPLATES_DIR
    pytest.skip("No copier-templates checkout available")


@pytest.mark.integration
def test_theme_barceloneta_generates_and_tests_pass(tmp_path: Path) -> None:
    if shutil.which("uv") is None:
        pytest.skip("uv is required for the integration test")

    templates_dir = _templates_dir()
    config = PlonecliConfig(templates_dir=str(templates_dir))

    package_name = "collective.mythemetest"
    project_dir = tmp_path / package_name
    theme_name = "My Test Theme"

    # 1. Generate the backend_addon — pre-fill every answer so copier runs
    #    non-interactively.
    run_create(
        "backend_addon",
        str(project_dir),
        config,
        data={
            "package_name": package_name,
            "package_title": "My Theme Test",
            "package_description": "Integration test addon",
            "plone_version": "6.1",
            "is_headless": False,
            "author_name": "Plone Developer",
            "author_email": "dev@plone.org",
        },
    )
    assert (project_dir / "pyproject.toml").exists()

    # 2. Add the theme_barceloneta subtemplate.
    project = find_project_root(project_dir)
    assert project is not None, "backend_addon not detected after create"
    run_add(
        "theme_barceloneta",
        project,
        config,
        data={
            "theme_name": theme_name,
            "theme_description": "Integration test theme",
        },
    )

    # The template ships a theme test keyed on theme_id.
    theme_test = project_dir / "tests" / "test_theme_my_test_theme.py"
    assert theme_test.exists(), f"theme test not generated: {theme_test}"

    # 3. Build the project with uv sync + run its pytest suite. This is the
    #    step that takes minutes on a cold cache.
    env = os.environ.copy()
    env.pop("VIRTUAL_ENV", None)
    env.setdefault("PIP_DISABLE_PIP_VERSION_CHECK", "1")
    subprocess.run(
        ["uv", "sync", "--extra", "test"],
        cwd=project_dir,
        env=env,
        check=True,
    )

    result = subprocess.run(
        ["uv", "run", "--extra", "test", "pytest", "tests/", "-x", "-q"],
        cwd=project_dir,
        env=env,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"Generated package tests failed.\n"
        f"STDOUT:\n{result.stdout}\n"
        f"STDERR:\n{result.stderr}"
    )

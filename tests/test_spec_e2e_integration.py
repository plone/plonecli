"""End-to-end test: scaffold an addon from a spec, lint and test the result.

Generates a backend_addon plus a representative set of features from a single
declarative spec (the ``plonecli apply`` contract), then:

* runs ``ruff check`` — the generated tree must be lint-clean with zero edits;
* builds the package with ``uv sync --extra test`` and runs its own pytest
  suite inside a real Plone instance.

It is slow (builds Plone via ``uv sync``) and needs network on first run, so it
is marked ``integration`` and deselected by default. Run explicitly with::

    uv run pytest -m integration tests/test_spec_e2e_integration.py
"""

from __future__ import annotations

import os
import shutil
import subprocess
import textwrap
from pathlib import Path

import pytest

from plonecli.config import PlonecliConfig
from plonecli.project import find_project_root
from plonecli.spec import load_spec, validate_spec
from plonecli.templates import run_add, run_create

DEV_TEMPLATES_DIR = Path("/home/node/develop/plone/src/copier-templates")
FALLBACK_TEMPLATES_DIR = Path("/home/node/.copier-templates/plone-copier-templates")


def _templates_dir() -> Path:
    env_dir = os.environ.get("PLONECLI_TEMPLATES_DIR")
    if env_dir and Path(env_dir).exists():
        return Path(env_dir)
    if DEV_TEMPLATES_DIR.exists():
        return DEV_TEMPLATES_DIR
    if FALLBACK_TEMPLATES_DIR.exists():
        return FALLBACK_TEMPLATES_DIR
    pytest.skip("No copier-templates checkout available")


SPEC = """\
addon:
  template: backend_addon
  name: collective.spectest
  data:
    package_name: collective.spectest
features:
  - template: content_type
    data: {content_type_name: Todos, global_allow: true}
  - template: content_type
    data: {content_type_name: Todo, global_allow: false, parent_content_type: Todos}
  - template: behavior
    data: {behavior_name: IFeatured}
  - template: restapi_service
    data: {service_name: stats}
  - template: view
    data: {view_name: my-view}
  - template: language
    data: {language_code: de, language_name: German}
"""


def _apply_spec(spec, config, target_dir: Path) -> None:
    """Generate the spec's addon + features (mirrors ``plonecli apply``)."""
    run_create(
        spec.template,
        str(target_dir),
        config,
        data=spec.data,
        defaults=True,
    )
    project = find_project_root(target_dir)
    assert project is not None, "addon not detected after create"
    for feat in spec.features:
        run_add(feat.template, project, config, data=feat.data, defaults=True)


@pytest.mark.integration
def test_spec_scaffold_is_clean_and_tests_pass(tmp_path: Path) -> None:
    if shutil.which("uv") is None:
        pytest.skip("uv is required for the integration test")

    templates_dir = _templates_dir()
    config = PlonecliConfig(templates_dir=str(templates_dir))

    spec_file = tmp_path / "spec.yaml"
    spec_file.write_text(textwrap.dedent(SPEC))
    spec = load_spec(spec_file)
    assert validate_spec(spec, config) == [], "spec should validate"

    project_dir = tmp_path / spec.name
    _apply_spec(spec, config, project_dir)
    assert (project_dir / "pyproject.toml").exists()

    env = os.environ.copy()
    env.pop("VIRTUAL_ENV", None)
    env.setdefault("PIP_DISABLE_PIP_VERSION_CHECK", "1")

    # Lint: the generated tree must be ruff-clean with no hand-edits.
    lint = subprocess.run(
        ["uvx", "ruff", "check", "."],
        cwd=project_dir,
        env=env,
        capture_output=True,
        text=True,
    )
    assert lint.returncode == 0, (
        f"generated tree not ruff-clean:\n{lint.stdout}\n{lint.stderr}"
    )

    # Build + run the generated package's own test suite inside Plone.
    subprocess.run(
        ["uv", "sync", "--extra", "test"],
        cwd=project_dir,
        env=env,
        check=True,
    )
    result = subprocess.run(
        ["uv", "run", "--extra", "test", "pytest", "tests/", "-q"],
        cwd=project_dir,
        env=env,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"Generated package tests failed.\n"
        f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
    )

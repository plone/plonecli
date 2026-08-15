"""End-to-end test for the ``addon`` composite template.

``plonecli create addon <name>`` is a composite that applies ``backend_addon``
followed by ``zope-setup``. The ``zope-setup`` step runs a copier task that
invokes the ``zope_instance`` template to generate the initial Zope instance.

This test drives the real ``create`` CLI command against the local
copier-templates clone and asserts the initial instance lands on disk at
``var/instance/etc/zope.ini`` -- proving the full composite chain runs, not
just the step ordering covered by the unit tests.

It shells out to ``uv``/``copier`` and needs the templates clone, so it is
marked ``integration`` and deselected by default. Run explicitly with::

    uv run pytest -m integration tests/test_addon_composite_integration.py
"""

from __future__ import annotations

import shutil
from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from plonecli.cli import cli
from plonecli.config import PlonecliConfig
from tests.helpers import templates_checkout


@pytest.mark.integration
def test_create_addon_generates_initial_instance(tmp_path: Path) -> None:
    if shutil.which("uv") is None:
        pytest.skip("uv is required for the integration test")

    templates_dir = templates_checkout("addon/copier.yml")
    config = PlonecliConfig(templates_dir=str(templates_dir))
    project_dir = tmp_path / "my.tool"

    runner = CliRunner()
    # Patch only the clone (avoid network); the composite resolution, both
    # template steps and the instance-creating copier task all run for real.
    with (
        patch("plonecli.cli.load_config", return_value=config),
        patch("plonecli.cli.ensure_templates_cloned"),
    ):
        result = runner.invoke(
            cli,
            ["create", "addon", str(project_dir), "--defaults"],
            catch_exceptions=False,
        )

    assert result.exit_code == 0, result.output

    # backend_addon step produced the package.
    assert (project_dir / "pyproject.toml").exists(), result.output

    # zope-setup step produced the initial Zope instance.
    zope_ini = project_dir / "var" / "instance" / "etc" / "zope.ini"
    assert zope_ini.exists(), (
        f"initial instance not generated at {zope_ini}\n{result.output}"
    )
    assert (project_dir / "var" / "instance" / "etc" / "zope.conf").exists()
    assert "egg:Zope#main" in zope_ini.read_text()

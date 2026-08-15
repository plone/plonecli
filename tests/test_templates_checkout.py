"""Tests for locating a copier-templates checkout in the test suite.

The integration tests are worthless if they cannot find the checkout: pytest
reports them as passed/skipped either way, so a wrong lookup silently empties
the sweep instead of failing.
"""

from pathlib import Path

import pytest

from tests import helpers
from tests.helpers import find_templates_checkout, templates_checkout

MARKER = "backend_addon/copier.yml"


def _fake_checkout(path: Path, marker: str = MARKER) -> Path:
    (path / marker).parent.mkdir(parents=True, exist_ok=True)
    (path / marker).write_text("{}\n")
    return path


def _isolate(monkeypatch, tmp_path):
    """Point every non-explicit candidate at somewhere that does not exist."""
    monkeypatch.delenv("PLONECLI_TEMPLATES_DIR", raising=False)
    monkeypatch.setattr(helpers, "DEV_TEMPLATES_DIR", tmp_path / "missing-dev")
    monkeypatch.setattr(helpers, "LEGACY_TEMPLATES_DIRS", [])
    monkeypatch.setattr(
        helpers,
        "PlonecliConfig",
        lambda: type("C", (), {"templates_dir": str(tmp_path / "missing-config")})(),
    )


def test_env_var_wins(monkeypatch, tmp_path):
    _isolate(monkeypatch, tmp_path)
    env_dir = _fake_checkout(tmp_path / "env")
    _fake_checkout(tmp_path / "dev")
    monkeypatch.setattr(helpers, "DEV_TEMPLATES_DIR", tmp_path / "dev")
    monkeypatch.setenv("PLONECLI_TEMPLATES_DIR", str(env_dir))

    assert find_templates_checkout() == env_dir


def test_repo_development_checkout_is_a_candidate(monkeypatch, tmp_path):
    """AGENTS.md puts the checkout at develop/plone/src/copier-templates."""
    _isolate(monkeypatch, tmp_path)
    dev_dir = _fake_checkout(tmp_path / "dev")
    monkeypatch.setattr(helpers, "DEV_TEMPLATES_DIR", dev_dir)

    assert find_templates_checkout() == dev_dir


def test_repo_development_path_matches_agents_md():
    assert (
        helpers.DEV_TEMPLATES_DIR
        == helpers.REPO_ROOT / "develop" / "plone" / "src" / "copier-templates"
    )


def test_configured_clone_is_a_candidate(monkeypatch, tmp_path):
    _isolate(monkeypatch, tmp_path)
    clone = _fake_checkout(tmp_path / "clone")
    monkeypatch.setattr(
        helpers,
        "PlonecliConfig",
        lambda: type("C", (), {"templates_dir": str(clone)})(),
    )

    assert find_templates_checkout() == clone


def test_marker_must_be_present(monkeypatch, tmp_path):
    """A directory without the requested template is not a usable checkout."""
    _isolate(monkeypatch, tmp_path)
    checkout = _fake_checkout(tmp_path / "backend-only")
    monkeypatch.setenv("PLONECLI_TEMPLATES_DIR", str(checkout))

    assert find_templates_checkout() == checkout
    assert find_templates_checkout("addon/copier.yml") is None


def test_returns_none_and_skips_when_nothing_is_available(monkeypatch, tmp_path):
    _isolate(monkeypatch, tmp_path)

    assert find_templates_checkout() is None
    with pytest.raises(pytest.skip.Exception):
        templates_checkout()


def test_template_sweep_is_populated_when_a_checkout_exists():
    """The regression itself: a found checkout must yield real parameters."""
    from tests.test_all_templates_data import _all_templates

    if find_templates_checkout() is None:
        pytest.skip("No copier-templates checkout available")

    names = [name for name, _ in _all_templates()]
    assert "backend_addon" in names
    assert len(names) > 5

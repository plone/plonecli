"""Shared test helpers."""

import os
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from plonecli.config import PlonecliConfig

REPO_ROOT = Path(__file__).resolve().parent.parent

# Where this repository keeps its development checkout of copier-templates.
DEV_TEMPLATES_DIR = REPO_ROOT / "develop" / "plone" / "src" / "copier-templates"

# Devcontainer locations kept as a last resort.
LEGACY_TEMPLATES_DIRS = [
    "/home/node/develop/plone/src/copier-templates",
    "/home/node/.copier-templates/plone-copier-templates",
]


def project_at(path, project_type="backend_addon"):
    """A stand-in ProjectContext rooted at ``path``."""
    return MagicMock(
        root_folder=path,
        project_type=project_type,
        package_name="test.addon",
        package_folder="test/addon",
        settings={},
    )


def _templates_candidates():
    """Ordered candidate locations for a copier-templates checkout."""
    return [
        os.environ.get("PLONECLI_TEMPLATES_DIR"),
        DEV_TEMPLATES_DIR,
        PlonecliConfig().templates_dir,
        *LEGACY_TEMPLATES_DIRS,
    ]


def find_templates_checkout(marker="backend_addon/copier.yml"):
    """First candidate checkout containing ``marker``, or None.

    Safe to call at collection time: it never skips.
    """
    for candidate in _templates_candidates():
        if candidate and (Path(candidate) / marker).exists():
            return Path(candidate)
    return None


def templates_checkout(marker="backend_addon/copier.yml"):
    """Like :func:`find_templates_checkout`, but skips the test when missing."""
    path = find_templates_checkout(marker)
    if path is None:
        pytest.skip(f"No copier-templates checkout with {marker} available")
    return path

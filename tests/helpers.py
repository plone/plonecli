"""Shared test helpers."""

from unittest.mock import MagicMock


def project_at(path, project_type="backend_addon"):
    """A stand-in ProjectContext rooted at ``path``."""
    return MagicMock(
        root_folder=path,
        project_type=project_type,
        package_name="test.addon",
        package_folder="test/addon",
        settings={},
    )

"""Project detection via pyproject.toml."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ProjectContext:
    root_folder: Path
    project_type: str  # "backend_addon" or "project"
    settings: dict
    package_name: str | None = None
    package_folder: str | None = None


def _read_backend_addon_settings(pyproject_path: Path) -> dict | None:
    """Read [tool.plone.backend_addon.settings] from pyproject.toml."""
    try:
        with open(pyproject_path, "rb") as f:
            doc = tomllib.load(f)
        settings = (
            doc.get("tool", {})
            .get("plone", {})
            .get("backend_addon", {})
            .get("settings", {})
        )
        if settings:
            return dict(settings)
    except (tomllib.TOMLDecodeError, OSError):
        pass
    return None


def _read_project_settings(pyproject_path: Path) -> dict | None:
    """Read [tool.plone.project.settings] from pyproject.toml."""
    try:
        with open(pyproject_path, "rb") as f:
            doc = tomllib.load(f)
        settings = (
            doc.get("tool", {})
            .get("plone", {})
            .get("project", {})
            .get("settings", {})
        )
        if settings:
            result = dict(settings)
            # Include project name if not in settings
            project = doc.get("project", {})
            if "project_name" not in result and "name" in project:
                result["project_name"] = project["name"]
            return result
    except (tomllib.TOMLDecodeError, OSError):
        pass
    return None


def find_project_root(start_dir: Path | None = None) -> ProjectContext | None:
    """Walk up directories looking for a Plone project pyproject.toml.

    Detects two project types:
    - [tool.plone.backend_addon.settings] -> backend_addon
    - [tool.plone.project.settings] -> project (zope-setup)

    Returns the first match found walking upward, or None.
    """
    current = (start_dir or Path.cwd()).resolve()

    while True:
        pyproject_path = current / "pyproject.toml"
        if pyproject_path.exists():
            # Check for backend_addon first
            addon_settings = _read_backend_addon_settings(pyproject_path)
            if addon_settings:
                return ProjectContext(
                    root_folder=current,
                    project_type="backend_addon",
                    settings=addon_settings,
                    package_name=addon_settings.get("package_name"),
                    package_folder=addon_settings.get("package_folder"),
                )

            # Check for zope-setup project
            project_settings = _read_project_settings(pyproject_path)
            if project_settings:
                return ProjectContext(
                    root_folder=current,
                    project_type="project",
                    settings=project_settings,
                )

        parent = current.parent
        if parent == current:
            break
        current = parent

    return None

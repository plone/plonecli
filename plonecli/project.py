"""Project detection via pyproject.toml or bobtemplate.cfg."""

from __future__ import annotations

import configparser
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


# Mapping from bobtemplate.cfg template names to plonecli project types
_BOBTEMPLATE_TYPE_MAP: dict[str, str] = {
    "plone_addon": "backend_addon",
    "plone_theme": "backend_addon",
}


def _read_bobtemplate_cfg(cfg_path: Path) -> ProjectContext | None:
    """Read bobtemplate.cfg (old mr.bob style) and return a ProjectContext.

    Expected format::

        [main]
        template = plone_addon

    The template value is mapped to a plonecli project type.
    Package name and folder are inferred from the directory name.
    """
    parser = configparser.ConfigParser()
    try:
        parser.read(str(cfg_path))
    except configparser.Error:
        return None

    if not parser.has_section("main"):
        return None

    template = parser.get("main", "template", fallback=None)
    if not template:
        return None

    project_type = _BOBTEMPLATE_TYPE_MAP.get(template)
    if not project_type:
        return None

    root_folder = cfg_path.parent
    # Infer package info from directory name (e.g. "lmu.geozentrum")
    dir_name = root_folder.name
    package_name = dir_name
    package_folder = dir_name.replace(".", "/")

    settings = {"package_name": package_name, "package_folder": package_folder}

    return ProjectContext(
        root_folder=root_folder,
        project_type=project_type,
        settings=settings,
        package_name=package_name,
        package_folder=package_folder,
    )


def find_project_root(start_dir: Path | None = None) -> ProjectContext | None:
    """Walk up directories looking for a Plone project.

    Detection order (first match wins):
    1. pyproject.toml with [tool.plone.backend_addon.settings] -> backend_addon
    2. pyproject.toml with [tool.plone.project.settings] -> project (zope-setup)
    3. bobtemplate.cfg with [main] template -> mapped project type (legacy)

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

        # Check for legacy bobtemplate.cfg
        bobtemplate_path = current / "bobtemplate.cfg"
        if bobtemplate_path.exists():
            ctx = _read_bobtemplate_cfg(bobtemplate_path)
            if ctx:
                return ctx

        parent = current.parent
        if parent == current:
            break
        current = parent

    return None

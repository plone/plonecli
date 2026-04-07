"""Git clone management and copier API wrapper for copier-templates."""

from __future__ import annotations

import subprocess
from pathlib import Path

from copier import run_copy

from plonecli.config import PlonecliConfig
from plonecli.project import ProjectContext


# Template alias mapping: user-facing name -> directory in clone
TEMPLATE_ALIASES: dict[str, str] = {
    "addon": "backend_addon",
    "backend_addon": "backend_addon",
    "zope_setup": "zope-setup",
    "zope-setup": "zope-setup",
}

# Main templates (used with `plonecli create`)
MAIN_TEMPLATES = {"backend_addon", "zope-setup"}

# Subtemplates per parent project type (used with `plonecli add`)
SUBTEMPLATES: dict[str, list[str]] = {
    "backend_addon": ["behavior", "content_type", "restapi_service"],
    "project": ["zope_instance"],
}


def resolve_template_name(alias: str) -> str | None:
    """Resolve a user-provided template alias to the canonical directory name.

    Returns None if the alias is unknown.
    """
    # Check aliases first
    if alias in TEMPLATE_ALIASES:
        return TEMPLATE_ALIASES[alias]
    # Check if it's already a valid directory name
    all_templates = MAIN_TEMPLATES | {
        t for subs in SUBTEMPLATES.values() for t in subs
    }
    if alias in all_templates:
        return alias
    return None


def ensure_templates_cloned(config: PlonecliConfig) -> Path:
    """Ensure the copier-templates repo is cloned locally.

    Performs a shallow clone on first run. Returns the path to the clone.
    """
    templates_dir = Path(config.templates_dir)
    if templates_dir.exists() and (templates_dir / ".git").exists():
        return templates_dir

    templates_dir.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "git",
            "clone",
            "--depth",
            "1",
            "--branch",
            config.repo_branch,
            config.repo_url,
            str(templates_dir),
        ],
        check=True,
    )
    return templates_dir


def update_templates_clone(config: PlonecliConfig) -> str:
    """Update the local copier-templates clone via git pull.

    Returns a status message.
    """
    templates_dir = Path(config.templates_dir)
    if not templates_dir.exists():
        ensure_templates_cloned(config)
        return "Templates cloned successfully."

    result = subprocess.run(
        ["git", "pull", "--ff-only"],
        cwd=str(templates_dir),
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return f"Failed to update templates: {result.stderr.strip()}"

    output = result.stdout.strip()
    if "Already up to date" in output:
        return "Templates already up to date."
    return f"Templates updated: {output}"


def get_template_path(template_name: str, config: PlonecliConfig) -> Path:
    """Get the full filesystem path to a template directory in the clone."""
    resolved = resolve_template_name(template_name)
    if resolved is None:
        msg = f"Unknown template: {template_name}"
        raise ValueError(msg)

    templates_dir = Path(config.templates_dir)
    return templates_dir / resolved


def get_templates_info(config: PlonecliConfig) -> str:
    """Get version info (git commit) from the templates clone."""
    templates_dir = Path(config.templates_dir)
    if not templates_dir.exists():
        return "not cloned"

    result = subprocess.run(
        ["git", "log", "-1", "--format=%h %ai"],
        cwd=str(templates_dir),
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        return result.stdout.strip()
    return "unknown"


def _build_user_defaults(config: PlonecliConfig) -> dict:
    """Build user_defaults dict from global config for copier."""
    defaults = {}
    if config.author_name and config.author_name != "Plone Developer":
        defaults["author_name"] = config.author_name
    if config.author_email and config.author_email != "dev@plone.org":
        defaults["author_email"] = config.author_email

    return defaults


def run_create(
    template_name: str,
    target_name: str,
    config: PlonecliConfig,
    data: dict | None = None,
) -> None:
    """Run copier to create a new project from a main template.

    Args:
        template_name: Template alias or directory name.
        target_name: Output directory name.
        config: Global plonecli configuration.
        data: Optional answers to pre-fill (skips interactive prompts for these).
    """
    ensure_templates_cloned(config)
    src = str(get_template_path(template_name, config))

    run_copy(
        src_path=src,
        dst_path=target_name,
        data=data or {},
        user_defaults=_build_user_defaults(config),
        unsafe=True,
    )


def run_add(
    template_name: str,
    project: ProjectContext,
    config: PlonecliConfig,
    data: dict | None = None,
) -> None:
    """Run copier to add a subtemplate to an existing project.

    Args:
        template_name: Subtemplate name.
        project: Detected project context.
        config: Global plonecli configuration.
        data: Optional extra answers.
    """
    ensure_templates_cloned(config)
    src = str(get_template_path(template_name, config))

    # Pre-populate package info from project context
    template_data = {}
    if project.package_name:
        template_data["package_name"] = project.package_name
    if project.package_folder:
        template_data["package_folder"] = project.package_folder
    if data:
        template_data.update(data)

    run_copy(
        src_path=src,
        dst_path=str(project.root_folder),
        data=template_data,
        user_defaults=_build_user_defaults(config),
        unsafe=True,
    )

"""Template discovery from local copier-templates clone."""

from __future__ import annotations

from pathlib import Path

import yaml

from plonecli.config import PlonecliConfig
from plonecli.project import ProjectContext
from plonecli.templates import MAIN_TEMPLATES, SUBTEMPLATES, TEMPLATE_ALIASES


def _read_template_metadata(copier_yml: Path) -> dict:
    """Read _plonecli metadata from a copier.yml file.

    Expected format in copier.yml:
        _plonecli:
            template_type: main | sub
            parent_types:
                - backend_addon
            aliases:
                - upgrade

    Returns an empty dict if no _plonecli section is found.
    """
    try:
        with open(copier_yml) as f:
            data = yaml.safe_load(f)
        if isinstance(data, dict):
            return data.get("_plonecli", {}) or {}
    except (OSError, yaml.YAMLError):
        pass
    return {}


class TemplateRegistry:
    """Discovers available templates by scanning the local clone for copier.yml files.

    Templates can self-register by adding a ``_plonecli`` section to their
    ``copier.yml``.  This is merged with the hardcoded fallback lists in
    ``plonecli.templates`` so that new templates work without a plonecli release.
    """

    def __init__(
        self,
        config: PlonecliConfig,
        project: ProjectContext | None = None,
    ):
        self.config = config
        self.project = project
        self.templates_dir = Path(config.templates_dir)
        # Cache for discovered metadata (populated lazily)
        self._metadata_cache: dict[str, dict] | None = None

    # ------------------------------------------------------------------
    # Discovery helpers
    # ------------------------------------------------------------------

    def _discover_templates(self) -> list[str]:
        """Scan the templates directory for subdirectories with copier.yml."""
        if not self.templates_dir.exists():
            return []
        templates = []
        for entry in sorted(self.templates_dir.iterdir()):
            if entry.is_dir() and (entry / "copier.yml").exists():
                templates.append(entry.name)
        return templates

    def _get_metadata(self) -> dict[str, dict]:
        """Return cached mapping of template_name -> _plonecli metadata."""
        if self._metadata_cache is not None:
            return self._metadata_cache

        self._metadata_cache = {}
        if not self.templates_dir.exists():
            return self._metadata_cache

        for entry in sorted(self.templates_dir.iterdir()):
            copier_yml = entry / "copier.yml"
            if entry.is_dir() and copier_yml.exists():
                self._metadata_cache[entry.name] = _read_template_metadata(
                    copier_yml,
                )
        return self._metadata_cache

    # ------------------------------------------------------------------
    # Dynamic alias resolution
    # ------------------------------------------------------------------

    def _build_aliases(self) -> dict[str, str]:
        """Build alias -> canonical name mapping from hardcoded + dynamic sources."""
        aliases = dict(TEMPLATE_ALIASES)
        for name, meta in self._get_metadata().items():
            for alias in meta.get("aliases", []):
                aliases[alias] = name
            # Every template name maps to itself
            aliases[name] = name
        return aliases

    # ------------------------------------------------------------------
    # Template classification
    # ------------------------------------------------------------------

    def get_main_templates(self) -> list[str]:
        """List templates available for ``plonecli create``."""
        discovered = self._discover_templates()
        result = []
        for name in discovered:
            meta = self._get_metadata().get(name, {})
            template_type = meta.get("template_type")
            if template_type == "main" or (
                template_type is None and name in MAIN_TEMPLATES
            ):
                result.append(name)
        return result

    def get_subtemplates(self) -> list[str]:
        """List templates available for ``plonecli add``.

        Context-aware: returns subtemplates valid for the detected project type.
        """
        if not self.project:
            return []

        project_type = self.project.project_type
        discovered = self._discover_templates()
        # Hardcoded fallback list for this project type
        hardcoded = set(SUBTEMPLATES.get(project_type, []))

        result = []
        for name in discovered:
            meta = self._get_metadata().get(name, {})
            template_type = meta.get("template_type")
            parent_types = meta.get("parent_types", [])

            if template_type == "sub" and project_type in parent_types:
                # Dynamically registered subtemplate
                result.append(name)
            elif template_type is None and name in hardcoded:
                # Fallback to hardcoded list
                result.append(name)
        return result

    def get_available_templates(self) -> list[str]:
        """Context-aware template list.

        Returns main templates if outside a project, subtemplates if inside.
        """
        if self.project:
            return self.get_subtemplates()
        return self.get_main_templates()

    def is_main_template(self, resolved_name: str) -> bool:
        """Check if a resolved template name is a main template."""
        return resolved_name in self.get_main_templates()

    def is_subtemplate(self, resolved_name: str) -> bool:
        """Check if a resolved template name is a valid subtemplate for the current project."""
        return resolved_name in self.get_subtemplates()

    def list_templates(self) -> str:
        """Return a formatted string of all available templates for display."""
        lines = ["Available templates:"]

        main = self.get_main_templates()
        if main:
            lines.append("")
            lines.append("  Project templates (plonecli create <template> <name>):")
            for t in main:
                # Show user-friendly aliases
                aliases = self._build_aliases()
                alias_list = [a for a, v in aliases.items() if v == t and a != t]
                alias_str = f" (alias: {alias_list[0]})" if alias_list else ""
                lines.append(f"    - {t}{alias_str}")

                # Show subtemplates for this project type
                project_type = t if t in SUBTEMPLATES else "project"
                # Also check dynamic subtemplates
                subs = self._get_subtemplates_for_type(project_type)
                if subs:
                    for s in subs:
                        lines.append(f"        - {s}")

        if self.project:
            subs = self.get_subtemplates()
            if subs:
                lines.append("")
                lines.append("  Feature templates (plonecli add <template>):")
                for s in subs:
                    lines.append(f"    - {s}")

        return "\n".join(lines)

    def _get_subtemplates_for_type(self, project_type: str) -> list[str]:
        """Get all subtemplates for a given project type (for display purposes)."""
        discovered = self._discover_templates()
        hardcoded = set(SUBTEMPLATES.get(project_type, []))
        result = []
        for name in discovered:
            meta = self._get_metadata().get(name, {})
            template_type = meta.get("template_type")
            parent_types = meta.get("parent_types", [])
            if template_type == "sub" and project_type in parent_types:
                result.append(name)
            elif template_type is None and name in hardcoded:
                result.append(name)
        return result

    def resolve_template_name(self, alias: str) -> str | None:
        """Resolve a user-provided alias to a canonical template directory name."""
        aliases = self._build_aliases()
        if alias in aliases:
            return aliases[alias]
        # Check if it's a valid template name directly
        discovered = self._discover_templates()
        if alias in discovered:
            return alias
        return None

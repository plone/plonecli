"""Template discovery from local copier-templates clone."""

from __future__ import annotations

from pathlib import Path

from plonecli.config import PlonecliConfig
from plonecli.project import ProjectContext
from plonecli.templates import MAIN_TEMPLATES, SUBTEMPLATES, TEMPLATE_ALIASES


class TemplateRegistry:
    """Discovers available templates by scanning the local clone for copier.yml files."""

    def __init__(
        self,
        config: PlonecliConfig,
        project: ProjectContext | None = None,
    ):
        self.config = config
        self.project = project
        self.templates_dir = Path(config.templates_dir)

    def _discover_templates(self) -> list[str]:
        """Scan the templates directory for subdirectories with copier.yml."""
        if not self.templates_dir.exists():
            return []
        templates = []
        for entry in sorted(self.templates_dir.iterdir()):
            if entry.is_dir() and (entry / "copier.yml").exists():
                templates.append(entry.name)
        return templates

    def get_main_templates(self) -> list[str]:
        """List templates available for `plonecli create`."""
        discovered = self._discover_templates()
        return [t for t in discovered if t in MAIN_TEMPLATES]

    def get_subtemplates(self) -> list[str]:
        """List templates available for `plonecli add`.

        Context-aware: returns subtemplates valid for the detected project type.
        """
        if not self.project:
            return []
        allowed = SUBTEMPLATES.get(self.project.project_type, [])
        discovered = self._discover_templates()
        return [t for t in discovered if t in allowed]

    def get_available_templates(self) -> list[str]:
        """Context-aware template list.

        Returns main templates if outside a project, subtemplates if inside.
        """
        if self.project:
            return self.get_subtemplates()
        return self.get_main_templates()

    def list_templates(self) -> str:
        """Return a formatted string of all available templates for display."""
        lines = ["Available templates:"]

        main = self.get_main_templates()
        if main:
            lines.append("")
            lines.append("  Project templates (plonecli create <template> <name>):")
            for t in main:
                # Show user-friendly aliases
                aliases = [a for a, v in TEMPLATE_ALIASES.items() if v == t and a != t]
                alias_str = f" (alias: {aliases[0]})" if aliases else ""
                lines.append(f"    - {t}{alias_str}")

                # Show subtemplates for this project type
                project_type = "backend_addon" if t == "backend_addon" else "project"
                subs = SUBTEMPLATES.get(project_type, [])
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

    def resolve_template_name(self, alias: str) -> str | None:
        """Resolve a user-provided alias to a canonical template directory name."""
        if alias in TEMPLATE_ALIASES:
            return TEMPLATE_ALIASES[alias]
        # Check if it's a valid template name directly
        discovered = self._discover_templates()
        if alias in discovered:
            return alias
        return None

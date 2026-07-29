"""Install the bundled plonecli Agent Skills into a project or user config.

The skills ship inside this package under ``plonecli/skills/<name>`` and follow
the Agent Skills open standard, so the exact same ``SKILL.md`` files are loaded
by Claude Code, Codex, Gemini CLI, Cursor and other compatible agents.

Installation places one real copy per skill at ``<base>/.agents/skills/<name>``
(the open-standard discovery path) and exposes it to Claude Code via a relative
symlink at ``<base>/.claude/skills/<name>``. ``base`` is the project root for
``project`` scope or the user's home for ``user`` scope.
"""

from __future__ import annotations

import os
import shutil
from dataclasses import dataclass
from pathlib import Path

AGENTS_DIR = Path(".agents") / "skills"
CLAUDE_DIR = Path(".claude") / "skills"


@dataclass
class Action:
    kind: str  # "copy" | "symlink"
    target: Path
    points_to: str | None = None


def get_source_skills_root() -> Path:
    """Path to the skills bundled inside the installed plonecli package."""
    return Path(__file__).resolve().parent / "skills"


def bundled_skill_names() -> list[str]:
    """Names of all bundled skills (directories containing a SKILL.md)."""
    root = get_source_skills_root()
    if not root.is_dir():
        return []
    return sorted(p.name for p in root.iterdir() if (p / "SKILL.md").is_file())


def resolve_base(scope: str, project_root: Path | None) -> Path:
    """Resolve the base directory the skills are installed under."""
    if scope == "user":
        return Path.home()
    if project_root is not None:
        return Path(project_root)
    return Path.cwd()


def _remove_existing(path: Path) -> None:
    if path.is_symlink() or path.is_file():
        path.unlink()
    elif path.is_dir():
        shutil.rmtree(path)


def _copy_tree(source: Path, target: Path) -> Action:
    _remove_existing(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, target)
    return Action("copy", target)


def _link_or_copy(source: Path, target: Path, copy_only: bool) -> Action:
    """Make ``target`` a relative symlink to ``source``, falling back to a copy."""
    _remove_existing(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    if copy_only or os.name == "nt":
        return _copy_tree(source, target)
    rel = os.path.relpath(source, target.parent)
    try:
        target.symlink_to(rel, target_is_directory=True)
        return Action("symlink", target, rel)
    except OSError:
        return _copy_tree(source, target)


def install_skill(
    scope: str = "project",
    project_root: Path | None = None,
    copy_only: bool = False,
    force: bool = False,
    update: bool = False,
) -> tuple[Path, list[Action]]:
    """Install or refresh all bundled skills under the resolved base directory.

    Returns the base dir and the list of filesystem actions performed.
    """
    names = bundled_skill_names()
    if not names:
        raise FileNotFoundError(
            f"No bundled skills found under {get_source_skills_root()}"
        )

    base = resolve_base(scope, project_root)

    if not (force or update):
        for name in names:
            target = base / AGENTS_DIR / name
            if target.exists():
                raise FileExistsError(
                    f"Skill already installed at {target}. "
                    "Run 'plonecli skill update' or pass --force to overwrite."
                )

    actions = []
    for name in names:
        source = get_source_skills_root() / name
        agents_target = base / AGENTS_DIR / name
        claude_target = base / CLAUDE_DIR / name
        actions.append(_copy_tree(source, agents_target))
        actions.append(_link_or_copy(agents_target, claude_target, copy_only))
    return base, actions


def skill_status(scope: str, project_root: Path | None) -> dict:
    """Report where the bundled skills are installed under the resolved base."""
    base = resolve_base(scope, project_root)

    def describe(path: Path) -> str:
        if path.is_symlink():
            return f"symlink -> {os.readlink(path)}"
        if path.is_dir():
            return "copy"
        return "not installed"

    skills = {}
    for name in bundled_skill_names():
        agents_target = base / AGENTS_DIR / name
        claude_target = base / CLAUDE_DIR / name
        skills[name] = {
            "agents": (agents_target, describe(agents_target)),
            "claude": (claude_target, describe(claude_target)),
        }
    return {
        "base": base,
        "source": get_source_skills_root(),
        "skills": skills,
    }

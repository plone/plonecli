"""Install the bundled plonecli Agent Skill into a project or user config.

The skill ships inside this package at ``plonecli/skills/plonecli`` and follows
the Agent Skills open standard, so the exact same ``SKILL.md`` is loaded by
Claude Code, Codex, Gemini CLI, Cursor and other compatible agents.

Installation places one real copy at ``<base>/.agents/skills/plonecli`` (the
open-standard discovery path) and exposes it to Claude Code via a relative
symlink at ``<base>/.claude/skills/plonecli``. ``base`` is the project root for
``project`` scope or the user's home for ``user`` scope.
"""

from __future__ import annotations

import os
import shutil
from dataclasses import dataclass
from pathlib import Path

SKILL_NAME = "plonecli"
AGENTS_REL = Path(".agents") / "skills" / SKILL_NAME
CLAUDE_REL = Path(".claude") / "skills" / SKILL_NAME


@dataclass
class Action:
    kind: str  # "copy" | "symlink"
    target: Path
    points_to: str | None = None


def get_source_skill_dir() -> Path:
    """Path to the skill bundled inside the installed plonecli package."""
    return Path(__file__).resolve().parent / "skills" / SKILL_NAME


def resolve_base(scope: str, project_root: Path | None) -> Path:
    """Resolve the base directory the skill is installed under."""
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
    """Install or refresh the skill under the resolved base directory.

    Returns the base dir and the list of filesystem actions performed.
    """
    source = get_source_skill_dir()
    if not source.is_dir():
        raise FileNotFoundError(f"Bundled skill not found at {source}")

    base = resolve_base(scope, project_root)
    agents_target = base / AGENTS_REL
    claude_target = base / CLAUDE_REL

    if agents_target.exists() and not (force or update):
        raise FileExistsError(
            f"Skill already installed at {agents_target}. "
            "Run 'plonecli skill update' or pass --force to overwrite."
        )

    actions = [_copy_tree(source, agents_target)]
    actions.append(_link_or_copy(agents_target, claude_target, copy_only))
    return base, actions


def skill_status(scope: str, project_root: Path | None) -> dict:
    """Report where the skill is installed under the resolved base."""
    base = resolve_base(scope, project_root)
    agents_target = base / AGENTS_REL
    claude_target = base / CLAUDE_REL

    def describe(path: Path) -> str:
        if path.is_symlink():
            return f"symlink -> {os.readlink(path)}"
        if path.is_dir():
            return "copy"
        return "not installed"

    return {
        "base": base,
        "source": get_source_skill_dir(),
        "agents": (agents_target, describe(agents_target)),
        "claude": (claude_target, describe(claude_target)),
    }

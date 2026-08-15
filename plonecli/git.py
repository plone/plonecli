"""Auto-commit support for generated packages.

plonecli initialises a git repository in every generated package and commits
after each template run, so the package always has a reviewable history and
subtemplate runs are easy to inspect or revert. This mirrors the auto-commit
behaviour of the legacy ``bobtemplates.plone``. Users can opt out per run with
``--no-git`` or globally via the ``auto_commit`` config setting.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from plonecli.config import PlonecliConfig
from plonecli.output import error


def is_git_repo(path: Path) -> bool:
    """Return True if ``path`` is the root of a git working tree."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=str(path),
            check=True,
            capture_output=True,
            text=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False
    return Path(result.stdout.strip()).resolve() == path.resolve()


def dirty_files(path: str | Path) -> tuple[list[str], list[str]]:
    """Return ``(modified, untracked)`` paths for the git repo at ``path``.

    Both lists are empty when the working tree is clean or ``path`` is not a
    git repository.
    """
    path = Path(path)
    if not is_git_repo(path):
        return [], []

    result = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=str(path),
        capture_output=True,
        text=True,
    )
    modified: list[str] = []
    untracked: list[str] = []
    for line in result.stdout.splitlines():
        if not line.strip():
            continue
        code = line[:2]
        name = line[3:]
        if code.startswith("?"):
            untracked.append(name)
        else:
            modified.append(name)
    return modified, untracked


def _has_identity(path: Path) -> bool:
    """Return True if git has both user.name and user.email configured."""
    for key in ("user.name", "user.email"):
        result = subprocess.run(
            ["git", "config", key],
            cwd=str(path),
            capture_output=True,
            text=True,
        )
        if not result.stdout.strip():
            return False
    return True


def _nothing_staged(path: Path) -> bool:
    """Return True if the index has no staged changes to commit."""
    result = subprocess.run(
        ["git", "diff", "--cached", "--quiet"],
        cwd=str(path),
    )
    return result.returncode == 0


def commit_template_changes(
    target_dir: str | Path,
    template_name: str,
    config: PlonecliConfig,
    *,
    is_subtemplate: bool,
) -> str | None:
    """Initialise git (if needed) and commit the result of a template run.

    Args:
        target_dir: The generated/updated package directory.
        template_name: Canonical template name, used in the commit message.
        config: Global plonecli config (provides the identity fallback).
        is_subtemplate: Whether this was an ``add`` (subtemplate) run.

    Returns:
        The commit message if a commit was made, otherwise ``None`` (nothing to
        commit). Git failures are swallowed with a warning so a generated
        package is never lost to a git problem.
    """
    target = Path(target_dir)
    if not target.exists():
        return None

    try:
        just_initialized = False
        if not is_git_repo(target):
            subprocess.run(
                ["git", "init"],
                cwd=str(target),
                check=True,
                capture_output=True,
            )
            just_initialized = True

        subprocess.run(
            ["git", "add", "-A"],
            cwd=str(target),
            check=True,
            capture_output=True,
        )

        if _nothing_staged(target):
            return None

        if is_subtemplate:
            message = f"Add {template_name} subtemplate"
        elif just_initialized:
            message = f"Create package with {template_name} template"
        else:
            message = f"Add {template_name} template"

        commit_cmd = ["git"]
        if not _has_identity(target):
            commit_cmd += [
                "-c",
                f"user.name={config.author_name}",
                "-c",
                f"user.email={config.author_email}",
            ]
        commit_cmd += ["commit", "-m", message]
        subprocess.run(
            commit_cmd,
            cwd=str(target),
            check=True,
            capture_output=True,
        )
        return message
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        error(
            f"ERROR: git auto-commit failed ({exc}).\n"
            f"The generated files in {target} are uncommitted - commit them "
            f"yourself."
        )
        return None

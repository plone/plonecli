"""Git clone management and copier API wrapper for copier-templates."""

from __future__ import annotations

import subprocess
from pathlib import Path

from copier import run_copy
from copier._main import Worker
from copier.errors import UserMessageError

from plonecli.config import PlonecliConfig
from plonecli.exceptions import TemplateRunError
from plonecli.git import commit_template_changes
from plonecli.output import echo
from plonecli.project import ProjectContext
from plonecli.registry import _read_template_metadata


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
    """Update the local copier-templates clone.

    Fetches from origin and hard-resets to the configured branch. The clone is
    plonecli-managed, so divergence (e.g. from an upstream rebase or force-push)
    is resolved by resetting to ``origin/<branch>`` rather than attempting a
    merge.
    """
    templates_dir = Path(config.templates_dir)
    if not templates_dir.exists():
        ensure_templates_cloned(config)
        return "Templates cloned successfully."

    branch = config.repo_branch
    subprocess.run(
        ["git", "fetch", "--depth", "1", "origin", branch],
        cwd=str(templates_dir),
        check=True,
        capture_output=True,
        text=True,
    )

    before = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=str(templates_dir),
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    after = subprocess.run(
        ["git", "rev-parse", f"origin/{branch}"],
        cwd=str(templates_dir),
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()

    if before == after:
        return "Templates already up to date."

    subprocess.run(
        ["git", "reset", "--hard", f"origin/{branch}"],
        cwd=str(templates_dir),
        check=True,
        capture_output=True,
        text=True,
    )
    return f"Templates updated: {before[:7]} → {after[:7]}"


def get_template_path(template_name: str, config: PlonecliConfig) -> Path:
    """Get the full filesystem path to a template directory in the clone.

    ``template_name`` must already be a canonical directory name (resolve any
    user-supplied alias via ``TemplateRegistry.resolve_template_name`` first).
    """
    templates_dir = Path(config.templates_dir)
    path = templates_dir / template_name
    if not path.exists():
        msg = f"Unknown template: {template_name}"
        raise ValueError(msg)
    return path


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
    defaults: bool = False,
    git_commit: bool = True,
    overwrite: bool = False,
) -> str | None:
    """Run copier to create a new project from a main template.

    Args:
        template_name: Template alias or directory name.
        target_name: Output directory name.
        config: Global plonecli configuration.
        data: Optional answers to pre-fill (skips interactive prompts for these).
        defaults: Use template defaults for unanswered questions instead of
            prompting (non-interactive mode).
        git_commit: Initialise git (if needed) and commit the result.
        overwrite: Overwrite existing files without prompting. Needed when a
            template is layered onto an existing project (composite steps after
            the first, ``plonecli setup``); copier otherwise raises an
            interactive-conflict error in non-interactive mode.

    Returns:
        The commit message if a commit was made, otherwise ``None``.
    """
    ensure_templates_cloned(config)
    src = str(get_template_path(template_name, config))

    run_copy(
        src_path=src,
        dst_path=target_name,
        data=data or {},
        user_defaults=_build_user_defaults(config),
        defaults=defaults,
        overwrite=overwrite,
        unsafe=True,
    )

    if git_commit:
        return commit_template_changes(
            target_name, template_name, config, is_subtemplate=False
        )
    return None


def _recording_worker(conflicts: list[Path]) -> type[Worker]:
    """A copier Worker that records conflicting files instead of writing them."""

    class RecordingWorker(Worker):
        def _solve_render_conflict(self, dst_relpath: Path) -> bool:
            if self.match_skip(dst_relpath) or dst_relpath == self.answers_relpath:
                return super()._solve_render_conflict(dst_relpath)
            conflicts.append(dst_relpath)
            return False

    return RecordingWorker


def _conflict_message(conflicts: list[Path]) -> str:
    paths = ", ".join(str(path) for path in conflicts)
    verb = "exists" if len(conflicts) == 1 else "exist"
    return f"{paths} {verb}; pass --overwrite or --skip-existing"


def _copy(on_conflict: str, **kwargs) -> Worker:
    if on_conflict == "fail":
        conflicts: list[Path] = []
        with _recording_worker(conflicts)(
            **kwargs, pretend=True, quiet=True, skip_tasks=True
        ) as probe:
            probe.run_copy()
        if conflicts:
            raise TemplateRunError(_conflict_message(conflicts))
    if on_conflict == "skip":
        skipped: list[Path] = []
        with _recording_worker(skipped)(**kwargs) as worker:
            worker.run_copy()
        for path in skipped:
            echo(f"  kept existing {path}", fg="yellow")
        return worker
    return run_copy(**kwargs, overwrite=on_conflict == "overwrite")


def _commit_message(template_dir: Path, answers) -> str | None:
    template = _read_template_metadata(template_dir / "copier.yml")
    try:
        return template.get("commit_message", "").format_map(answers) or None
    except (KeyError, IndexError, ValueError):
        return None


def run_add(
    template_name: str,
    project: ProjectContext,
    config: PlonecliConfig,
    data: dict | None = None,
    defaults: bool = False,
    git_commit: bool = True,
    on_conflict: str = "ask",
) -> str | None:
    """Run copier to add a subtemplate to an existing project.

    Args:
        template_name: Subtemplate name.
        project: Detected project context.
        config: Global plonecli configuration.
        data: Optional extra answers.
        defaults: Use template defaults for unanswered questions instead of
            prompting (non-interactive mode).
        git_commit: Initialise git (if needed) and commit the result.
        on_conflict: How to treat existing files that differ from the render:
            ``ask`` (copier prompts), ``fail`` (abort before writing anything),
            ``overwrite`` or ``skip``.

    Returns:
        The commit message if a commit was made, otherwise ``None``.
    """
    ensure_templates_cloned(config)
    src = get_template_path(template_name, config)

    # Pre-populate package info from project context
    template_data = {}
    if project.package_name:
        template_data["package_name"] = project.package_name
    if project.package_folder:
        template_data["package_folder"] = project.package_folder
    if data:
        template_data.update(data)

    try:
        worker = _copy(
            on_conflict,
            src_path=str(src),
            dst_path=Path(project.root_folder),
            data=template_data,
            user_defaults=_build_user_defaults(config),
            defaults=defaults,
            unsafe=True,
        )
    except UserMessageError as exc:
        raise TemplateRunError(str(exc).strip() or type(exc).__name__) from exc
    except ValueError as exc:
        if not str(exc).startswith("Validation error"):
            raise
        raise TemplateRunError(str(exc)) from exc

    if git_commit:
        return commit_template_changes(
            project.root_folder,
            template_name,
            config,
            is_subtemplate=True,
            message=_commit_message(src, worker.answers.combined),
        )
    return None

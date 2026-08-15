#!/usr/bin/env python3
"""Verify plonecli auto-commit: every command leaves the project repo clean.

The scaffolding matrix in ``run_evals.py`` runs everything with ``--no-git`` so
that generated trees stay disposable. That leaves the auto-commit path — the
behaviour users actually get by default — untested. This harness is the
complement: it runs the same commands *with* git enabled and asserts, after
every command, that

- the generated project is a git repository,
- ``git status --porcelain`` is empty, and
- the run produced the expected new commit.

Reports land in ``results-git/report.json`` and ``results-git/report.md``.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from run_evals import (  # noqa: E402
    BACKEND_SUBTEMPLATES,
    CLI,
    ROOT,
    TEMPLATES,
    backend_data,
    data_args,
    individual_data,
    provenance,
    zope_data,
)

HERE = Path(__file__).resolve().parent
WORKSPACES = HERE / "workspaces-git"
RESULTS = HERE / "results-git"
LOGS = RESULTS / "logs"


def git(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
    )


def porcelain(repo: Path) -> list[str]:
    return [line for line in git(repo, "status", "--porcelain").stdout.splitlines()]


def commit_subjects(repo: Path) -> list[str]:
    result = git(repo, "log", "--format=%s")
    if result.returncode != 0:
        return []
    return result.stdout.splitlines()


def run(cmd: list[str], cwd: Path, env: dict[str, str], log: Path, timeout: int):
    started = time.monotonic()
    completed = subprocess.run(
        cmd,
        cwd=str(cwd),
        env=env,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    log.write_text(
        f"$ {' '.join(cmd)}\n(cwd={cwd})\n\n--- stdout ---\n{completed.stdout}\n"
        f"--- stderr ---\n{completed.stderr}\n",
        encoding="utf-8",
    )
    return completed, time.monotonic() - started


class Recorder:
    def __init__(self) -> None:
        self.results: list[dict[str, Any]] = []

    def record(self, case_id: str, problems: list[str], detail: dict[str, Any]) -> None:
        status = "passed" if not problems else "failed"
        reason = f" -- {'; '.join(problems)}" if problems else ""
        print(f"  {status}: {case_id}{reason}")
        self.results.append(
            {
                "id": case_id,
                "status": status,
                "problems": problems,
                **detail,
            }
        )


def exit_problems(completed: subprocess.CompletedProcess) -> list[str]:
    """A one-entry problem list when the command itself failed."""
    if completed.returncode == 0:
        return []
    return [f"exit={completed.returncode}"]


def check_repo(
    repo: Path, expect_commit: str | None, before: list[str]
) -> tuple[list[str], dict[str, Any]]:
    """Return (problems, detail) for the repo state after a command."""
    problems: list[str] = []
    if not (repo / ".git").exists():
        return ["no git repository was initialised"], {"dirty": [], "commits": []}

    dirty = porcelain(repo)
    after = commit_subjects(repo)
    if dirty:
        problems.append(f"working tree dirty after the command: {dirty[:8]}")
    if expect_commit is not None:
        new = after[: len(after) - len(before)]
        if not new:
            problems.append("no new commit was created")
        elif expect_commit not in new[0]:
            problems.append(
                f"commit subject {new[0]!r} does not mention {expect_commit!r}"
            )
    return problems, {"dirty": dirty, "commits": after}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timeout", type=int, default=900)
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Only the project-level cases, skipping the per-subtemplate sweep.",
    )
    args = parser.parse_args()

    shutil.rmtree(WORKSPACES, ignore_errors=True)
    shutil.rmtree(RESULTS, ignore_errors=True)
    WORKSPACES.mkdir(parents=True)
    LOGS.mkdir(parents=True)

    env = dict(os.environ)
    env["PLONECLI_TEMPLATES_DIR"] = str(TEMPLATES)
    env["PYTHONUNBUFFERED"] = "1"
    # A deterministic identity so the commit path never depends on the machine.
    env.setdefault("GIT_AUTHOR_NAME", "Eval Runner")
    env.setdefault("GIT_AUTHOR_EMAIL", "eval@example.invalid")
    env.setdefault("GIT_COMMITTER_NAME", "Eval Runner")
    env.setdefault("GIT_COMMITTER_EMAIL", "eval@example.invalid")

    rec = Recorder()
    started = time.monotonic()

    # --- create backend_addon -------------------------------------------------
    print("create cases")
    backend_root = WORKSPACES / "create-backend"
    backend_root.mkdir()
    target = backend_root / "collective.gitbackend"
    cmd = [
        *CLI,
        "create",
        "backend_addon",
        str(target),
        "--defaults",
        "--allow-dirty",
        *data_args(backend_data("collective.gitbackend")),
    ]
    completed, _ = run(cmd, ROOT, env, LOGS / "create-backend_addon.log", args.timeout)
    problems = exit_problems(completed)
    repo_problems, detail = check_repo(target, "backend_addon", [])
    rec.record("create-backend_addon", problems + repo_problems, detail)

    # --- skill install --scope project ----------------------------------------
    # Writes into the project tree, so it falls under the same contract.
    if (target / ".git").exists():
        before = commit_subjects(target)
        cmd = [*CLI, "skill", "install", "--scope", "project"]
        completed, _ = run(cmd, target, env, LOGS / "skill-install.log", args.timeout)
        problems = exit_problems(completed)
        repo_problems, detail = check_repo(target, "plonecli skills", before)
        rec.record("skill-install", problems + repo_problems, detail)

    # --- create zope-setup ----------------------------------------------------
    zope_root = WORKSPACES / "create-zope"
    zope_root.mkdir()
    zope_target = zope_root / "gitzope"
    cmd = [
        *CLI,
        "create",
        "zope-setup",
        str(zope_target),
        "--defaults",
        "--allow-dirty",
        *data_args(zope_data("gitzope")),
    ]
    completed, _ = run(cmd, ROOT, env, LOGS / "create-zope-setup.log", args.timeout)
    problems = exit_problems(completed)
    repo_problems, detail = check_repo(zope_target, "zope-setup", [])
    rec.record("create-zope-setup", problems + repo_problems, detail)

    # --- create addon composite ----------------------------------------------
    composite_root = WORKSPACES / "create-composite"
    composite_root.mkdir()
    composite_target = composite_root / "collective.gitcomposite"
    # plone_version is omitted: the backend template asks for a minor version and
    # zope-setup for a full version, so one value cannot satisfy both choices.
    merged = {
        **backend_data("collective.gitcomposite"),
        **zope_data("collective.gitcomposite"),
    }
    data = {key: value for key, value in merged.items() if key != "plone_version"}
    cmd = [
        *CLI,
        "create",
        "addon",
        str(composite_target),
        "--defaults",
        "--allow-dirty",
        *data_args(data),
    ]
    completed, _ = run(cmd, ROOT, env, LOGS / "create-addon.log", args.timeout)
    problems = exit_problems(completed)
    # The composite applies backend_addon then zope-setup, so the newest commit
    # names the last step and the history must hold one commit per step.
    repo_problems, detail = check_repo(composite_target, "zope-setup", [])
    if len(detail["commits"]) < 2:
        repo_problems.append(
            f"expected one commit per composite step, got {detail['commits']}"
        )
    rec.record("create-addon-composite", problems + repo_problems, detail)

    # --- setup ----------------------------------------------------------------
    print("setup case")
    setup_root = WORKSPACES / "setup"
    setup_root.mkdir()
    setup_target = setup_root / "collective.gitsetup"
    cmd = [
        *CLI,
        "create",
        "backend_addon",
        str(setup_target),
        "--defaults",
        "--allow-dirty",
        *data_args(backend_data("collective.gitsetup")),
    ]
    completed, _ = run(cmd, ROOT, env, LOGS / "setup-create.log", args.timeout)
    if completed.returncode != 0:
        rec.record("setup", [f"parent create failed exit={completed.returncode}"], {})
    else:
        before = commit_subjects(setup_target)
        cmd = [
            *CLI,
            "setup",
            "--defaults",
            "--allow-dirty",
            *data_args(zope_data("collective.gitsetup")),
        ]
        completed, _ = run(cmd, setup_target, env, LOGS / "setup.log", args.timeout)
        problems = exit_problems(completed)
        repo_problems, detail = check_repo(setup_target, "zope-setup", before)
        rec.record("setup", problems + repo_problems, detail)

    # --- add zope_instance into the standalone Zope project -------------------
    if not args.quick and (zope_target / ".git").exists():
        before = commit_subjects(zope_target)
        cmd = [
            *CLI,
            "add",
            "zope_instance",
            "--defaults",
            "--allow-dirty",
            *data_args(
                {
                    "instance_name": "git-extra",
                    "port": 8188,
                    "base_path": "runtime-extra",
                    "db_storage": "instance",
                    "initial_zope_username": "runner",
                    "initial_user_password": "not-a-real-password",
                }
            ),
        ]
        completed, _ = run(
            cmd, zope_target, env, LOGS / "add-zope_instance.log", args.timeout
        )
        problems = exit_problems(completed)
        repo_problems, detail = check_repo(zope_target, "zope_instance", before)
        rec.record("add-zope_instance", problems + repo_problems, detail)

    # --- add <subtemplate> ----------------------------------------------------
    if not args.quick:
        print("add cases")
        parent_root = WORKSPACES / "add-parent"
        parent_root.mkdir()
        parent = parent_root / "collective.gitparent"
        cmd = [
            *CLI,
            "create",
            "backend_addon",
            str(parent),
            "--defaults",
            "--allow-dirty",
            *data_args(backend_data("collective.gitparent")),
        ]
        completed, _ = run(cmd, ROOT, env, LOGS / "add-parent.log", args.timeout)
        if completed.returncode != 0:
            rec.record(
                "add-parent", [f"parent create failed exit={completed.returncode}"], {}
            )
        else:
            for index, template in enumerate(BACKEND_SUBTEMPLATES):
                case_root = WORKSPACES / "add" / template
                case_root.mkdir(parents=True)
                project = case_root / parent.name
                shutil.copytree(parent, project, symlinks=True)
                before = commit_subjects(project)
                cmd = [
                    *CLI,
                    "add",
                    template,
                    "--defaults",
                    "--allow-dirty",
                    *data_args(individual_data(template, index)),
                ]
                completed, _ = run(
                    cmd, project, env, LOGS / f"add-{template}.log", args.timeout
                )
                problems = exit_problems(completed)
                repo_problems, detail = check_repo(project, template, before)
                rec.record(f"add-{template}", problems + repo_problems, detail)

    elapsed = time.monotonic() - started
    failures = sum(r["status"] != "passed" for r in rec.results)
    report = {
        "elapsed_seconds": round(elapsed, 1),
        "provenance": provenance(),
        "counts": {
            "total": len(rec.results),
            "passed": len(rec.results) - failures,
            "failed": failures,
        },
        "cases": rec.results,
    }
    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    lines = [
        "# plonecli auto-commit evaluation",
        "",
        f"{report['counts']['passed']} passed, {failures} failed "
        f"in {report['elapsed_seconds']}s.",
        "",
        "| case | status | problems |",
        "| --- | --- | --- |",
    ]
    for case in rec.results:
        problems = "; ".join(case["problems"]).replace("|", "\\|") or "-"
        lines.append(f"| `{case['id']}` | {case['status']} | {problems} |")
    (RESULTS / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Wrote {RESULTS / 'report.md'}; failures={failures}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())

"""Behavioral evals for the bundled Agent Skills, as pytest tests.

Each test runs headless Claude Code in an isolated sandbox and grades the
command log / files mechanically — see evals/skill/README.md. The runs bill
real model usage, so they are gated: they only run with RUN_SKILL_EVALS=1 set
and the `claude` CLI installed, and are skipped otherwise.

    RUN_SKILL_EVALS=1 uv run --extra test pytest -m evals -v

SKILL_EVAL_MODEL overrides the evaluated model (default: sonnet).
For skill-vs-no-skill baselines use the CLI runner: evals/skill/run_evals.py
--mode both.
"""

import os
import shutil
import sys
import tempfile
import time
from pathlib import Path

import pytest

EVALS_DIR = Path(__file__).resolve().parent.parent / "evals" / "skill"
sys.path.insert(0, str(EVALS_DIR))

import run_evals  # noqa: E402

pytestmark = [
    pytest.mark.evals,
    pytest.mark.skipif(
        os.environ.get("RUN_SKILL_EVALS") != "1",
        reason="skill evals bill model usage; set RUN_SKILL_EVALS=1 to run",
    ),
    pytest.mark.skipif(
        shutil.which("claude") is None, reason="claude CLI not installed"
    ),
]


@pytest.fixture(scope="session")
def eval_env():
    # pid suffix: parallel tox envs (tox -m evals -p) must not share a root
    root = (
        Path(tempfile.gettempdir())
        / "plonecli-skill-evals"
        / f"{time.strftime('pytest-%Y%m%d-%H%M%S')}-{os.getpid()}"
    )
    root.mkdir(parents=True, exist_ok=True)
    skills = sorted(
        p for p in run_evals.SKILLS_SRC.iterdir() if (p / "SKILL.md").is_file()
    )
    assert skills, f"no bundled skills under {run_evals.SKILLS_SRC}"
    return {
        "root": root,
        "config": run_evals.make_eval_config(root),
        "skills": skills,
        "model": os.environ.get("SKILL_EVAL_MODEL", "sonnet"),
    }


@pytest.mark.parametrize("case", run_evals.CASES, ids=lambda c: c.id)
def test_skill_case(case, eval_env):
    result = run_evals.run_case(
        case,
        "skill",
        eval_env["root"],
        eval_env["model"],
        eval_env["skills"],
        eval_env["config"],
    )
    failed = [desc for desc, ok, extra in run_evals.grade(case, result) if not ok]
    assert not failed, (
        f"failed checks: {failed}"
        f"{'; run error: ' + result.error if result.error else ''}"
        f"; sandbox: {result.sandbox}"
    )

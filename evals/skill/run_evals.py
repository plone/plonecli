#!/usr/bin/env python3
"""Behavioral evals for the bundled plonecli Agent Skill.

Each case drops a fixture project into a sandbox, runs headless Claude Code
(`claude -p`) against a task prompt, and grades what the agent *did*: a shim
`plonecli` (and `uv run invoke`) on PATH logs every invocation instead of
really scaffolding, so runs are fast, hermetic and cheap.

Modes:
  skill    - the skill under --skill-src is installed project-scope
  noskill  - no skill at all (baseline: how much does the skill actually help?)
  both     - run each case in both modes and compare

Each run gets an isolated CLAUDE_CONFIG_DIR (credentials copied in, nothing
else), so user-scope skills and global CLAUDE.md never leak into the eval.

Usage:
  python evals/skill/run_evals.py --mode skill --model sonnet
  python evals/skill/run_evals.py --cases restapi-implicit,upgrade-step --mode both
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
SKILLS_SRC = REPO / "plonecli" / "skills"
FIXTURES = HERE / "fixtures"
SHIM = HERE / "shim"

RUN_TIMEOUT = 900  # seconds per case
MAX_TURNS = "40"


@dataclass
class RunResult:
    sandbox: Path
    log: str = ""  # shim command log ("<cwd> :: plonecli <args>")
    transcript: str = ""  # raw stream-json
    final_text: str = ""  # agent's final message
    error: str = ""
    skills_fired: tuple = ()


# ---------------------------------------------------------------- checks


def log_has(pattern, desc=None):
    def check(r):
        return bool(re.search(pattern, r.log, re.M))

    check.desc = desc or f"command log matches /{pattern}/"
    return check


def log_lacks(pattern, desc=None):
    def check(r):
        return not re.search(pattern, r.log, re.M)

    check.desc = desc or f"command log does NOT match /{pattern}/"
    return check


def file_has(relpath, pattern, desc=None):
    def check(r):
        p = r.sandbox / relpath
        return p.is_file() and bool(re.search(pattern, p.read_text(), re.M))

    check.desc = desc or f"{relpath} matches /{pattern}/"
    return check


def transcript_lacks(pattern, desc=None):
    def check(r):
        return not re.search(pattern, r.transcript)

    check.desc = desc or f"transcript does NOT match /{pattern}/"
    return check


@dataclass
class Case:
    id: str
    prompt: str
    fixture: str = ""  # subdir of fixtures/ copied into the sandbox
    checks: list = field(default_factory=list)
    notes: str = ""


CASES = [
    Case(
        id="create-addon",
        prompt=(
            "Create a new Plone backend add-on named collective.demo here. "
            "Package description: 'Demo add-on for talks'."
        ),
        checks=[
            log_has(
                r"plonecli create (backend_addon|addon) collective\.demo",
                "scaffolds via plonecli create",
            ),
            log_has(
                r"create .*--defaults", "runs create non-interactively (--defaults)"
            ),
        ],
        notes="Basic create flow; hand-writing the package skeleton is a fail.",
    ),
    Case(
        id="add-behavior",
        prompt=(
            "In the collective.demo add-on in this directory, add a behavior "
            "called IFeatured that can be enabled on content types."
        ),
        fixture="addon",
        checks=[
            log_has(
                r"plonecli add behavior(?=.*--defaults)(?=.*behavior_name=)",
                "scaffolds via plonecli add behavior --defaults -d behavior_name=...",
            ),
        ],
        notes=(
            "Explicit feature-add; hand-written behaviors/*.py without "
            "plonecli is a fail."
        ),
    ),
    Case(
        id="add-contenttype",
        prompt=(
            "In the collective.demo add-on in this directory, add a new "
            "content type called Speaker."
        ),
        fixture="addon",
        checks=[
            log_has(
                r"plonecli add content_type(?=.*--defaults)(?=.*content_type_name=)",
                "scaffolds via plonecli add content_type --defaults "
                "-d content_type_name=...",
            ),
        ],
        notes=(
            "Content types go through the subtemplate, not hand-written "
            "schema/FTI files."
        ),
    ),
    Case(
        id="add-vocabulary",
        prompt=(
            "Add a vocabulary named AudienceLevels to the collective.demo "
            "add-on in this directory."
        ),
        fixture="addon",
        checks=[
            log_has(
                r"plonecli add vocabulary(?=.*--defaults)(?=.*vocabulary_name=)",
                "scaffolds via plonecli add vocabulary --defaults "
                "-d vocabulary_name=...",
            ),
        ],
        notes="Vocabularies go through the subtemplate.",
    ),
    Case(
        id="add-view",
        prompt=(
            "Create a browser view called talk-listing for the collective.demo "
            "add-on in this directory."
        ),
        fixture="addon",
        checks=[
            log_has(
                r"plonecli add view(?=.*--defaults)(?=.*view_name=)",
                "scaffolds via plonecli add view --defaults -d view_name=...",
            ),
        ],
        notes="Browser views go through the subtemplate, not hand-written ZCML.",
    ),
    Case(
        id="restapi-implicit",
        prompt=(
            "Add a REST API endpoint @tasks to the collective.demo add-on "
            "in this directory."
        ),
        fixture="addon",
        checks=[
            log_has(
                r"plonecli add restapi_service(?=.*--defaults)(?=.*service_name=)",
                "scaffolds via plonecli add restapi_service "
                "(plonecli never mentioned in prompt)",
            ),
        ],
        notes=(
            "Invocation test: prompt never says 'plonecli' — the skill "
            "description must trigger."
        ),
    ),
    Case(
        id="fields-manual",
        prompt=(
            "In the collective.demo add-on in this directory, add two fields to "
            "the Talk content type: a required date field start_date, and an "
            "optional text-line field speaker."
        ),
        fixture="addon",
        checks=[
            file_has(
                "collective.demo/src/collective/demo/content/talk.py",
                r"start_date\s*=\s*(schema\.)?Date(time)?\(",
                "start_date added as Date field",
            ),
            file_has(
                "collective.demo/src/collective/demo/content/talk.py",
                r"speaker",
                "speaker field added",
            ),
            file_has(
                "collective.demo/src/collective/demo/content/talk.py",
                r"required=True",
                "start_date marked required",
            ),
            log_lacks(
                r"plonecli add \S*field",
                "no attempt to scaffold fields via a subtemplate",
            ),
        ],
        notes=(
            "Fields have no subtemplate — the plone-schema-fields skill "
            "must route to hand-editing."
        ),
    ),
    Case(
        id="upgrade-step",
        prompt=(
            "Add a boolean catalog index is_featured to the GenericSetup "
            "profile of the collective.demo add-on in this directory. Existing "
            "sites that already have the add-on installed must get the index too."
        ),
        fixture="addon",
        checks=[
            file_has(
                "collective.demo/src/collective/demo/profiles/default/catalog.xml",
                r"is_featured",
                "catalog.xml gains the index",
            ),
            log_has(
                r"plonecli add upgrade_step(?=.*--defaults)(?=.*upgrade_step_title=)",
                "scaffolds the upgrade step via plonecli",
            ),
        ],
        notes=(
            "Profile-XML rule: an edit that must reach installed sites "
            "needs plonecli add upgrade_step."
        ),
    ),
    Case(
        id="uninstall-mirror",
        prompt=(
            "Add a boolean catalog index is_featured to the GenericSetup "
            "profile of the collective.demo add-on in this directory, and make "
            "sure uninstalling the add-on cleans the index up again."
        ),
        fixture="addon",
        checks=[
            file_has(
                "collective.demo/src/collective/demo/profiles/default/catalog.xml",
                r"is_featured",
                "default catalog.xml gains the index",
            ),
            file_has(
                "collective.demo/src/collective/demo/profiles/uninstall/catalog.xml",
                r'is_featured(?s).*remove="True"|remove="True"(?s).*is_featured',
                "uninstall catalog.xml removes the index (remove=\"True\")",
            ),
        ],
        notes=(
            "Uninstall rule: a recreatable setting added to profiles/default "
            "must be mirrored for removal in profiles/uninstall."
        ),
    ),
    Case(
        id="no-serve",
        prompt=(
            "Start the Plone site of the collective.demo add-on in this "
            "directory so I can look at it in the browser."
        ),
        fixture="addon",
        checks=[
            log_lacks(r"plonecli (serve|debug)", "does not run plonecli serve/debug"),
            log_lacks(
                r"uv run invoke (start|debug)", "does not run invoke start/debug"
            ),
            transcript_lacks(
                r'"command":\s*"[^"]*invoke start', "no raw 'invoke start' either"
            ),
        ],
        notes=(
            "Server rule: the agent must ask the user to start the "
            "instance, never start it itself."
        ),
    ),
    Case(
        id="legacy-adapt",
        prompt=(
            "Use plonecli to add a vocabulary named AudienceLevels to the "
            "old.addon package in this directory."
        ),
        fixture="legacy",
        checks=[
            file_has(
                "old.addon/pyproject.toml",
                r"tool\.plone\.backend_addon\.settings",
                "adds the minimal settings block plonecli needs",
            ),
            log_has(
                r"plonecli add vocabulary", "then scaffolds via plonecli add vocabulary"
            ),
            log_lacks(
                r"plonecli create backend_addon",
                "does not re-run backend_addon over the package",
            ),
            file_has(
                "old.addon/src/old/addon/__init__.py",
                r"LEGACY-MARKER",
                "existing code preserved",
            ),
        ],
        notes=(
            "Legacy rule: minimal adaptation (settings block), never "
            "re-scaffold or hand-roll."
        ),
    ),
    Case(
        id="reconfigure",
        prompt=(
            "Change the package description of the collective.demo add-on in "
            "this directory to 'Conference management' using the project tooling."
        ),
        fixture="addon",
        checks=[
            log_has(r"uv run invoke reconfigure", "uses the reconfigure flow"),
            log_lacks(r"plonecli create", "does not re-run create over the project"),
        ],
        notes="Maintain rule: settings changes go through reconfigure, not re-create.",
    ),
]


# ---------------------------------------------------------------- plumbing


def make_eval_config(root):
    """Isolated CLAUDE_CONFIG_DIR: real credentials, no skills, no CLAUDE.md."""
    cfg = root / "claude-config"
    cfg.mkdir(parents=True, exist_ok=True)
    src = Path(os.environ.get("CLAUDE_CONFIG_DIR", str(Path.home() / ".claude")))
    creds = src / ".credentials.json"
    if creds.is_file():
        shutil.copy2(creds, cfg / ".credentials.json")
    return cfg


def prepare_sandbox(case, mode, root, skill_src):
    sandbox = root / f"{case.id}--{mode}"
    if sandbox.exists():
        shutil.rmtree(sandbox)
    sandbox.mkdir(parents=True)
    if case.fixture:
        src = FIXTURES / case.fixture
        for child in src.iterdir():
            dest = sandbox / child.name
            shutil.copytree(child, dest) if child.is_dir() else shutil.copy2(
                child, dest
            )
    if mode == "skill":
        for skill in skill_src:
            shutil.copytree(skill, sandbox / ".claude" / "skills" / skill.name)
    (sandbox / ".eval").mkdir()
    # Own git repo: pins the nested agent's project root to the sandbox
    # (no searching upward/sideways) and lets the shim's auto-commit work.
    subprocess.run(["git", "init", "-q"], cwd=sandbox, check=False)
    subprocess.run(["git", "add", "-A"], cwd=sandbox, check=False)
    subprocess.run(
        ["git", "commit", "-qm", "fixture"],
        cwd=sandbox,
        check=False,
        capture_output=True,
    )
    return sandbox


def run_case(case, mode, root, model, skill_src, config_dir):
    sandbox = prepare_sandbox(case, mode, root, skill_src)
    result = RunResult(sandbox=sandbox)
    log_file = sandbox / ".eval" / "commands.log"
    log_file.touch()

    env = os.environ.copy()
    env["PATH"] = f"{SHIM}:{env['PATH']}"
    env["PLONECLI_EVAL_LOG"] = str(log_file)
    env["CLAUDE_CONFIG_DIR"] = str(config_dir)

    cmd = [
        "claude",
        "-p",
        case.prompt,
        "--output-format",
        "stream-json",
        "--verbose",
        "--dangerously-skip-permissions",
        "--max-turns",
        MAX_TURNS,
    ]
    if model:
        cmd += ["--model", model]

    try:
        proc = subprocess.run(
            cmd,
            cwd=sandbox,
            env=env,
            capture_output=True,
            text=True,
            timeout=RUN_TIMEOUT,
        )
        result.transcript = proc.stdout
        if proc.returncode != 0:
            result.error = f"claude exited {proc.returncode}: {proc.stderr[-500:]}"
    except subprocess.TimeoutExpired as e:
        result.transcript = (
            (e.stdout or b"").decode()
            if isinstance(e.stdout, bytes)
            else (e.stdout or "")
        )
        result.error = f"timeout after {RUN_TIMEOUT}s"

    (sandbox / ".eval" / "transcript.jsonl").write_text(result.transcript)
    result.log = log_file.read_text()
    result.skills_fired = tuple(
        sorted(
            set(
                re.findall(r'"skill"\s*:\s*"(plone[\w-]*)"', result.transcript)
                + re.findall(r"skills/(plone[\w-]*)/SKILL\.md", result.transcript)
            )
        )
    )
    for line in result.transcript.splitlines():
        try:
            obj = json.loads(line)
        except ValueError:
            continue
        if obj.get("type") == "result":
            result.final_text = obj.get("result", "") or ""
    return result


def grade(case, result):
    rows = []
    for check in case.checks:
        try:
            ok = bool(check(result))
        except Exception as e:  # grading must never crash the harness
            ok = False
            rows.append((check.desc, ok, f"check error: {e}"))
            continue
        rows.append((check.desc, ok, ""))
    return rows


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--cases", help="comma-separated case ids (default: all)")
    ap.add_argument("--mode", choices=["skill", "noskill", "both"], default="skill")
    ap.add_argument(
        "--model",
        default="sonnet",
        help="model for the evaluated agent (default: sonnet; '' = user default)",
    )
    ap.add_argument(
        "--runs-dir",
        default=os.environ.get("PLONECLI_EVAL_RUNS", ""),
        help="where sandboxes go (default: <tmpdir>/plonecli-skill-evals/"
        "<timestamp>; must be OUTSIDE any git repo that contains "
        "the skill, or the baseline agent can find it)",
    )
    ap.add_argument(
        "--skill-src",
        default=str(SKILLS_SRC),
        help="skills to install in 'skill' mode: a directory of "
        "skill dirs, or a single skill dir with a SKILL.md "
        "(default: the repo's plonecli/skills; point at "
        "another checkout to A/B old vs new skills)",
    )
    ap.add_argument("--list", action="store_true", help="list cases and exit")
    args = ap.parse_args()

    if args.list:
        for c in CASES:
            print(f"{c.id:18} {c.notes}")
        return 0

    wanted = args.cases.split(",") if args.cases else [c.id for c in CASES]
    unknown = set(wanted) - {c.id for c in CASES}
    if unknown:
        ap.error(f"unknown case(s): {', '.join(sorted(unknown))}")
    cases = [c for c in CASES if c.id in wanted]
    modes = ["skill", "noskill"] if args.mode == "both" else [args.mode]

    stamp = time.strftime("%Y%m%d-%H%M%S")
    root = (
        Path(args.runs_dir)
        if args.runs_dir
        else Path(tempfile.gettempdir()) / "plonecli-skill-evals" / stamp
    )
    root.mkdir(parents=True, exist_ok=True)

    config_dir = make_eval_config(root)
    src = Path(args.skill_src)
    if (src / "SKILL.md").is_file():
        skill_src = [src]
    else:
        skill_src = sorted(p for p in src.iterdir() if (p / "SKILL.md").is_file())
    if not skill_src:
        ap.error(f"no SKILL.md found under --skill-src {src}")

    summary = []
    for case in cases:
        for mode in modes:
            print(f"\n=== {case.id} [{mode}] ===")
            t0 = time.time()
            result = run_case(
                case, mode, root, args.model or None, skill_src, config_dir
            )
            rows = grade(case, result)
            passed = all(ok for _, ok, _ in rows)
            for desc, ok, extra in rows:
                mark = "PASS" if ok else "FAIL"
                print(f"  [{mark}] {desc}{'  ' + extra if extra else ''}")
            if result.error:
                print(f"  [warn] {result.error}")
            print(
                f"  skills fired: {list(result.skills_fired) or 'none'} | "
                f"{time.time() - t0:.0f}s | sandbox: {result.sandbox}"
            )
            summary.append(
                {
                    "case": case.id,
                    "mode": mode,
                    "passed": passed,
                    "skills_fired": list(result.skills_fired),
                    "checks": [{"desc": d, "ok": ok} for d, ok, _ in rows],
                    "error": result.error,
                    "sandbox": str(result.sandbox),
                }
            )

    (root / "results.json").write_text(json.dumps(summary, indent=2))
    print(f"\nResults: {root / 'results.json'}")
    n_skill = [s for s in summary if s["mode"] == "skill"]
    if n_skill:
        n_ok = sum(s["passed"] for s in n_skill)
        print(f"skill mode: {n_ok}/{len(n_skill)} cases passed")
    n_base = [s for s in summary if s["mode"] == "noskill"]
    if n_base:
        print(
            f"baseline  : {sum(s['passed'] for s in n_base)}/{len(n_base)} cases passed"
        )
    return 0 if all(s["passed"] for s in n_skill) else 1


if __name__ == "__main__":
    sys.exit(main())

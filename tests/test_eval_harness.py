"""Fast correctness tests for the evaluation harnesses."""

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_scaffolding_validator_ignores_xml_tail_whitespace(tmp_path):
    validators = _load_module(
        "scaffolding_validators",
        ROOT / "evals" / "scaffolding" / "validators.py",
    )
    (tmp_path / "configure.zcml").write_text(
        '<configure><include package=".one" />\n  '
        '<include package=".one" /></configure>',
        encoding="utf-8",
    )

    errors = validators.detect_duplicate_xml_registrations(tmp_path)

    assert len(errors) == 1
    assert "duplicate XML registration (2x)" in errors[0]


def test_scaffolding_timeout_output_accepts_bytes(monkeypatch):
    scaffolding_dir = ROOT / "evals" / "scaffolding"
    monkeypatch.syspath_prepend(str(scaffolding_dir))
    runner = _load_module(
        "scaffolding_run_evals",
        scaffolding_dir / "run_evals.py",
    )

    assert runner._subprocess_text(b"partial \xff") == "partial �"
    assert runner._subprocess_text(None) == ""


def test_skill_uninstall_check_requires_name_and_remove_on_same_index(tmp_path):
    runner = _load_module(
        "skill_run_evals",
        ROOT / "evals" / "skill" / "run_evals.py",
    )
    package = tmp_path / "collective.demo" / "src" / "collective" / "demo"
    default = package / "profiles" / "default"
    uninstall = package / "profiles" / "uninstall"
    default.mkdir(parents=True)
    uninstall.mkdir(parents=True)
    (default / "catalog.xml").write_text("<index name='is_featured'/>")
    uninstall_xml = uninstall / "catalog.xml"
    case = next(case for case in runner.CASES if case.id == "uninstall-mirror")
    result = runner.RunResult(sandbox=tmp_path)

    uninstall_xml.write_text('<index name="is_featured"\n remove="True"/>')
    rows = runner.grade(case, result)
    assert all(ok for _, ok, _ in rows), rows

    uninstall_xml.write_text(
        '<indexes><index name="is_featured"/>'
        '<index name="other" remove="True"/></indexes>'
    )
    rows = runner.grade(case, result)
    assert rows[1][1] is False


def test_skill_run_errors_and_baseline_leaks_fail_the_run(tmp_path):
    runner = _load_module(
        "skill_run_evals_pass",
        ROOT / "evals" / "skill" / "run_evals.py",
    )
    passing_rows = [("check", True, "")]

    crashed = runner.RunResult(sandbox=tmp_path, error="timeout")
    leaked = runner.RunResult(sandbox=tmp_path, skills_fired=("plonecli",))

    assert runner.run_passed("skill", crashed, passing_rows) is False
    assert runner.run_passed("noskill", leaked, passing_rows) is False

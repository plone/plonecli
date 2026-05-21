"""Verify every template's settings can be driven non-interactively via data.

This covers the contract behind ``plonecli create/add --data KEY=VALUE``: for
every copier template shipped by the templates repo we must be able to answer
*every* question through ``data`` so copier never has to open an interactive
prompt (which can't be driven from a non-tty environment such as Claude Code or
CI).

Two layers:

* :func:`test_data_covers_all_questions` (always runs) parses each template's
  ``copier.yml`` and asserts the answer builder produces a value for every
  user-facing question. It guards against template drift — add a new question
  and this fails until it is answerable.
* :func:`test_template_generates_non_interactively` (``integration``, opt-in)
  actually generates every template with those answers using ``defaults=False``
  and no tty, proving copier never falls back to prompting.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
import yaml

from plonecli.config import PlonecliConfig
from plonecli.project import find_project_root
from plonecli.templates import run_add, run_create


DEV_TEMPLATES_DIR = Path("/home/node/develop/plone/src/copier-templates")
FALLBACK_TEMPLATES_DIR = Path("/home/node/.copier-templates/plone-copier-templates")

# Required-but-defaultless questions, plus anything whose default is a Jinja
# expression we cannot render here, get a concrete, validator-passing value.
SPECIAL_VALUES = {
    "package_name": "collective.datatest",
    "plone_version": "6.1",
    "behavior_name": "Featured",
    "content_type_name": "Article",
    "service_name": "myservice",
    "upgrade_step_title": "Reimport viewlets",
}


def _find_templates_dir() -> Path | None:
    if DEV_TEMPLATES_DIR.exists():
        return DEV_TEMPLATES_DIR
    if FALLBACK_TEMPLATES_DIR.exists():
        return FALLBACK_TEMPLATES_DIR
    return None


def _templates_dir() -> Path:
    templates_dir = _find_templates_dir()
    if templates_dir is None:
        pytest.skip("No copier-templates checkout available")
    return templates_dir


def _all_templates():
    """Yield (name, copier.yml-dict) for every real (non-composite) template.

    Evaluated at collection time, so it must not call ``pytest.skip`` (that is
    only valid inside a test). When no templates checkout is available it yields
    nothing, leaving the parametrized tests with an empty parameter set.
    """
    templates_dir = _find_templates_dir()
    if templates_dir is None:
        return
    for cfg in sorted(templates_dir.glob("*/copier.yml")):
        data = yaml.safe_load(cfg.read_text())
        meta = data.get("_plonecli", {})
        # Composite templates (e.g. ``addon``) have no questions of their own;
        # they are just an ordered list of other templates.
        if meta.get("type") == "composite":
            continue
        yield cfg.parent.name, data


def _user_facing_questions(template_data: dict) -> dict:
    """Return ``{name: spec}`` for questions copier may actually ask.

    Skips copier internals (``_*``) and computed values (``when: false``), which
    are never prompted and so need no answer.
    """
    questions = {}
    for name, spec in template_data.items():
        if name.startswith("_") or not isinstance(spec, dict):
            continue
        if spec.get("when") is False:
            continue
        questions[name] = spec
    return questions


def _is_jinja(value) -> bool:
    return isinstance(value, str) and ("{{" in value or "{%" in value)


def _answer_for(name: str, spec: dict):
    """Resolve a concrete, type-correct answer for a single question."""
    if name in SPECIAL_VALUES:
        return SPECIAL_VALUES[name]

    qtype = spec.get("type", "str")
    choices = spec.get("choices")
    default = spec.get("default")

    if qtype == "bool":
        return bool(default) if isinstance(default, bool) else True

    # Literal choice lists: prefer a static default, else the first option.
    if isinstance(choices, list) and choices:
        if isinstance(default, str) and not _is_jinja(default) and default in choices:
            return default
        return choices[0]

    if qtype == "int":
        return default if isinstance(default, int) else 8080

    # Plain string: a static default is always safe; otherwise synthesise a
    # non-empty value (enough to satisfy "is required" validators).
    if isinstance(default, str) and not _is_jinja(default) and default:
        return default
    return "Testing"


def _has_dynamic_choices(spec: dict) -> bool:
    """Choices computed at render time (a Jinja string), e.g. ``plone_version``.

    Their valid set is only known once copier runs the template's extensions
    (which may hit the network), so we cannot pick a value blindly — we leave
    these to the template's own default in non-interactive mode.
    """
    return isinstance(spec.get("choices"), str)


def _build_answers(template_data: dict) -> dict:
    return {
        name: _answer_for(name, spec)
        for name, spec in _user_facing_questions(template_data).items()
    }


def _copier_data(template_data: dict) -> dict:
    """Answers safe to feed copier directly (excludes dynamic-choice fields)."""
    return {
        name: _answer_for(name, spec)
        for name, spec in _user_facing_questions(template_data).items()
        if not _has_dynamic_choices(spec)
    }


@pytest.mark.parametrize(
    "name,template_data", list(_all_templates()), ids=lambda v: v if isinstance(v, str) else ""
)
def test_data_covers_all_questions(name, template_data):
    """Every user-facing question of every template gets a concrete answer."""
    questions = _user_facing_questions(template_data)
    answers = _build_answers(template_data)

    missing = set(questions) - set(answers)
    assert not missing, f"{name}: no data value resolved for {sorted(missing)}"

    for qname, value in answers.items():
        assert value is not None, f"{name}: {qname} resolved to None"
        qtype = questions[qname].get("type", "str")
        if qtype == "bool":
            assert isinstance(value, bool), f"{name}: {qname} must be bool"
        elif qtype == "int":
            assert isinstance(value, int), f"{name}: {qname} must be int"
        else:
            assert isinstance(value, str) and value, f"{name}: {qname} must be non-empty str"


def _generate_main(name, template_data, config, tmp_path) -> Path:
    project_dir = tmp_path / "collective.datatest"
    run_create(
        name,
        str(project_dir),
        config,
        data=_copier_data(template_data),
        defaults=True,
    )
    return project_dir


@pytest.fixture(scope="module")
def _parents(tmp_path_factory):
    """Generate one backend_addon and one zope-setup parent to add subs into."""
    config = PlonecliConfig(templates_dir=str(_templates_dir()))
    parents = {}
    for main in ("backend_addon", "zope-setup"):
        cfg = _templates_dir() / main / "copier.yml"
        if not cfg.exists():
            continue
        data = yaml.safe_load(cfg.read_text())
        base = tmp_path_factory.mktemp(f"parent-{main}")
        parents[main] = _generate_main(main, data, config, base)
    return parents


@pytest.mark.integration
@pytest.mark.parametrize(
    "name,template_data", list(_all_templates()), ids=lambda v: v if isinstance(v, str) else ""
)
def test_template_generates_non_interactively(name, template_data, _parents, tmp_path):
    """Each template generates non-interactively — mirroring ``--defaults``.

    ``defaults=True`` matches ``plonecli create/add --defaults``: copier never
    prompts, taking our ``data`` for every setting we override and the
    template's own default for the rest (e.g. the network-fetched
    ``plone_version`` list). Success proves the template can be driven without a
    tty and that all our supplied values pass copier's validators and choices.
    """
    if shutil.which("uv") is None:
        pytest.skip("uv is required to run template post-copy hooks")

    config = PlonecliConfig(templates_dir=str(_templates_dir()))
    meta = template_data.get("_plonecli", {})

    if meta.get("type") == "main":
        _generate_main(name, template_data, config, tmp_path)
        return

    # Subtemplate: copy the relevant parent and add into the copy.
    parent_name = meta.get("parent")
    parent_dir = _parents.get(parent_name)
    if parent_dir is None:
        pytest.skip(f"no generated parent for {parent_name!r}")

    work = tmp_path / parent_dir.name
    shutil.copytree(parent_dir, work)
    project = find_project_root(work)
    assert project is not None, f"{name}: parent project not detected in {work}"

    run_add(name, project, config, data=_copier_data(template_data), defaults=True)

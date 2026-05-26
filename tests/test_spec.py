"""Tests for the declarative spec (plonecli.spec) and the apply command."""

from __future__ import annotations

import textwrap

import pytest

from plonecli.config import PlonecliConfig
from plonecli.spec import (
    AddonSpec,
    FeatureSpec,
    SpecError,
    load_spec,
    validate_spec,
)


def _write(tmp_path, text):
    path = tmp_path / "spec.yaml"
    path.write_text(textwrap.dedent(text))
    return path


# --- fake template metadata -------------------------------------------------

BACKEND_QUESTIONS = {
    "package_name": {"type": "str", "default": "{{ x }}"},
    "plone_version": {"type": "str", "default": "6.1", "choices": ["6.0", "6.1"]},
    "is_headless": {"type": "bool", "default": False},
}

CONTENT_TYPE_QUESTIONS = {
    "content_type_name": {"type": "str"},  # required (no default)
    "global_allow": {"type": "bool", "default": True},
}


def _fake_questions(name, config):
    return {
        "backend_addon": BACKEND_QUESTIONS,
        "content_type": CONTENT_TYPE_QUESTIONS,
    }.get(name, {})


@pytest.fixture
def patched_registry(monkeypatch):
    """Patch registry classification + question loading with fakes."""
    import plonecli.spec as spec_mod

    monkeypatch.setattr(spec_mod, "_load_questions", _fake_questions)

    def resolve(self, alias):
        return alias if alias in {"backend_addon", "content_type"} else None

    monkeypatch.setattr(
        spec_mod.TemplateRegistry, "resolve_template_name", resolve, raising=True
    )
    monkeypatch.setattr(
        spec_mod.TemplateRegistry,
        "is_main_template",
        lambda self, n: n == "backend_addon",
        raising=True,
    )
    monkeypatch.setattr(
        spec_mod.TemplateRegistry,
        "get_main_templates",
        lambda self: ["backend_addon"],
        raising=True,
    )
    monkeypatch.setattr(
        spec_mod.TemplateRegistry,
        "get_composite_steps",
        lambda self, n: None,
        raising=True,
    )
    monkeypatch.setattr(
        spec_mod.TemplateRegistry,
        "_get_subtemplates_for_type",
        lambda self, t: ["content_type"] if t == "backend_addon" else [],
        raising=True,
    )


# --- load_spec --------------------------------------------------------------


def test_load_spec_minimal(tmp_path):
    path = _write(
        tmp_path,
        """
        addon:
          template: backend_addon
          name: collective.todo
        """,
    )
    spec = load_spec(path)
    assert spec == AddonSpec(
        template="backend_addon", name="collective.todo", data={}, features=[]
    )


def test_load_spec_with_features(tmp_path):
    path = _write(
        tmp_path,
        """
        addon:
          template: backend_addon
          name: collective.todo
          data:
            plone_version: "6.1"
        features:
          - template: content_type
            data:
              content_type_name: Todo
        """,
    )
    spec = load_spec(path)
    assert spec.data == {"plone_version": "6.1"}
    assert spec.features == [
        FeatureSpec(template="content_type", data={"content_type_name": "Todo"})
    ]


def test_load_spec_missing_addon(tmp_path):
    path = _write(tmp_path, "features: []\n")
    with pytest.raises(SpecError) as exc:
        load_spec(path)
    assert any("addon" in e for e in exc.value.errors)


def test_load_spec_missing_required_fields(tmp_path):
    path = _write(tmp_path, "addon:\n  data: {}\n")
    with pytest.raises(SpecError) as exc:
        load_spec(path)
    assert any("template" in e for e in exc.value.errors)
    assert any("name" in e for e in exc.value.errors)


def test_load_spec_not_a_mapping(tmp_path):
    path = _write(tmp_path, "- just\n- a\n- list\n")
    with pytest.raises(SpecError):
        load_spec(path)


# --- validate_spec ----------------------------------------------------------


def test_validate_spec_valid(patched_registry):
    spec = AddonSpec(
        template="backend_addon",
        name="collective.todo",
        data={"plone_version": "6.1"},
        features=[
            FeatureSpec(template="content_type", data={"content_type_name": "Todo"})
        ],
    )
    assert validate_spec(spec, PlonecliConfig()) == []


def test_validate_spec_unknown_main_template(patched_registry):
    spec = AddonSpec(template="bogus", name="x")
    errors = validate_spec(spec, PlonecliConfig())
    assert errors and "not a known project template" in errors[0]


def test_validate_spec_unknown_answer(patched_registry):
    spec = AddonSpec(
        template="backend_addon", name="x", data={"nope": "1"}
    )
    errors = validate_spec(spec, PlonecliConfig())
    assert any("unknown answer 'nope'" in e for e in errors)


def test_validate_spec_bad_choice(patched_registry):
    spec = AddonSpec(
        template="backend_addon", name="x", data={"plone_version": "9.9"}
    )
    errors = validate_spec(spec, PlonecliConfig())
    assert any("not in choices" in e for e in errors)


def test_validate_spec_missing_required_feature_answer(patched_registry):
    spec = AddonSpec(
        template="backend_addon",
        name="x",
        features=[FeatureSpec(template="content_type", data={})],
    )
    errors = validate_spec(spec, PlonecliConfig())
    assert any("missing required answer 'content_type_name'" in e for e in errors)


def test_validate_spec_invalid_feature_for_type(patched_registry):
    spec = AddonSpec(
        template="backend_addon",
        name="x",
        features=[FeatureSpec(template="bogus_feature", data={})],
    )
    errors = validate_spec(spec, PlonecliConfig())
    assert any("unknown template" in e for e in errors)

"""Declarative spec for scaffolding a complete addon non-interactively.

A spec is a single YAML file describing the main project template plus an
ordered list of feature subtemplates, so an agent can write one file and run
one command (``plonecli apply spec.yaml``). It is validated fail-fast against
the live template metadata *before* any files are generated.

Fields are intentionally out of scope: ``content_type``/``behavior`` emit an
empty schema and fields are added afterwards. The spec covers template/addon
options only.

Schema::

    addon:
      template: addon            # backend_addon | addon | zope-setup
      name: derico.todos         # target package/project name
      data:                      # answers for the main template
        plone_version: "6.1"
    features:                    # ordered subtemplates (optional)
      - template: content_type
        data:
          content_type_name: Todos
      - template: restapi_service
        data:
          service_name: "@todos"
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml

from plonecli.config import PlonecliConfig
from plonecli.registry import TemplateRegistry

# Main-template answers supplied implicitly by ``addon.name`` (copier derives
# them from the destination directory) or carrying a usable default.
_IMPLICIT_MAIN_ANSWERS = frozenset(
    {"package_name", "project_name", "project_title", "project_description"}
)

# Subtemplate answers ``run_add`` fills from the detected project context.
_IMPLICIT_FEATURE_ANSWERS = frozenset({"package_name", "package_folder"})


class SpecError(Exception):
    """Raised when a spec is malformed or fails validation.

    Carries a list of human-readable problems so the caller can show them all.
    """

    def __init__(self, errors: list[str]):
        self.errors = list(errors)
        super().__init__("\n".join(self.errors))


@dataclass
class FeatureSpec:
    template: str
    data: dict = field(default_factory=dict)


@dataclass
class AddonSpec:
    template: str
    name: str
    data: dict = field(default_factory=dict)
    features: list[FeatureSpec] = field(default_factory=list)


def load_spec(path: str | Path) -> AddonSpec:
    """Parse a spec file into an :class:`AddonSpec` (structure only).

    Raises :class:`SpecError` if the file is not a well-formed spec. Template
    existence and answer correctness are checked separately by
    :func:`validate_spec`.
    """
    path = Path(path)
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise SpecError([f"{path}: cannot read spec ({exc})"]) from exc
    except yaml.YAMLError as exc:
        raise SpecError([f"{path}: invalid YAML ({exc})"]) from exc

    if not isinstance(raw, dict):
        raise SpecError([f"{path}: spec must be a YAML mapping"])

    errors: list[str] = []
    addon = raw.get("addon")
    if not isinstance(addon, dict):
        raise SpecError([f"{path}: missing 'addon' section (a mapping)"])

    template = addon.get("template")
    name = addon.get("name")
    if not template:
        errors.append("addon.template is required")
    if not name:
        errors.append("addon.name is required")

    data = addon.get("data") or {}
    if not isinstance(data, dict):
        errors.append("addon.data must be a mapping")
        data = {}

    raw_features = raw.get("features") or []
    if not isinstance(raw_features, list):
        errors.append("features must be a list")
        raw_features = []

    features: list[FeatureSpec] = []
    for i, item in enumerate(raw_features):
        if not isinstance(item, dict):
            errors.append(f"features[{i}] must be a mapping")
            continue
        ftemplate = item.get("template")
        if not ftemplate:
            errors.append(f"features[{i}].template is required")
        fdata = item.get("data") or {}
        if not isinstance(fdata, dict):
            errors.append(f"features[{i}].data must be a mapping")
            fdata = {}
        if ftemplate:
            features.append(FeatureSpec(template=ftemplate, data=fdata))

    if errors:
        raise SpecError(errors)

    return AddonSpec(template=template, name=name, data=data, features=features)


def _load_questions(template_name: str, config: PlonecliConfig) -> dict:
    """Return ``{question_name: spec}`` for a template's declared questions.

    Skips copier internals (``_*``). Hidden/computed questions (``when: false``)
    are kept: they are not prompted, but copier still accepts them via ``--data``
    (e.g. ``behavior_marker``), so they are valid answer keys. :func:`_is_required`
    treats anything with a ``when`` as optional.
    """
    cfg = Path(config.templates_dir) / template_name / "copier.yml"
    if not cfg.exists():
        return {}
    try:
        data = yaml.safe_load(cfg.read_text()) or {}
    except (OSError, yaml.YAMLError):
        return {}
    questions = {}
    for name, spec in data.items():
        if name.startswith("_") or not isinstance(spec, dict):
            continue
        questions[name] = spec
    return questions


def _is_required(spec: dict) -> bool:
    """A question must be answered when it has no usable default.

    Conditional questions (a ``when`` expression) are treated as optional: they
    may not be asked at all. bool/int questions always have an effective value.
    """
    if "when" in spec:
        return False
    if spec.get("type") in ("bool", "int"):
        return False
    default = spec.get("default")
    return default is None or default == ""


def _choice_values(choices) -> list:
    """Normalise copier ``choices`` (list of scalars/dicts, or mapping) to values."""
    if isinstance(choices, dict):
        return list(choices.values())
    values = []
    for choice in choices:
        if isinstance(choice, dict):
            values.extend(choice.values())
        else:
            values.append(choice)
    return values


def _is_jinja(value) -> bool:
    return isinstance(value, str) and ("{{" in value or "{%" in value)


def _step_templates(main: str, reg: TemplateRegistry) -> list[str]:
    """Return the concrete templates a main template expands to."""
    steps = reg.get_composite_steps(main)
    return steps if steps else [main]


def _validate_answers(
    template_names: list[str],
    data: dict,
    config: PlonecliConfig,
    where: str,
    skip_required: frozenset = frozenset(),
) -> list[str]:
    """Validate ``data`` against the union of questions for ``template_names``."""
    errors: list[str] = []
    merged: dict = {}
    for name in template_names:
        merged.update(_load_questions(name, config))
    if not merged:
        # No metadata available (templates not cloned); cannot validate.
        return errors

    known = set(merged)
    for key in data:
        if key not in known:
            errors.append(
                f"{where}: unknown answer {key!r} "
                f"(template {'/'.join(template_names)})"
            )

    for qname, spec in merged.items():
        if qname in skip_required:
            continue
        if qname not in data:
            if _is_required(spec):
                errors.append(f"{where}: missing required answer {qname!r}")
            continue
        choices = spec.get("choices")
        if isinstance(choices, list) and choices:
            valid = _choice_values(choices)
            if any(_is_jinja(v) for v in valid):
                continue
            value = data[qname]
            valid_str = {str(v) for v in valid}
            if str(value) not in valid_str:
                errors.append(
                    f"{where}: {qname}={value!r} not in choices {sorted(valid_str)}"
                )
    return errors


def validate_spec(spec: AddonSpec, config: PlonecliConfig) -> list[str]:
    """Return a list of validation errors (empty when the spec is valid)."""
    errors: list[str] = []
    reg = TemplateRegistry(config)

    main = reg.resolve_template_name(spec.template)
    if main is None or not reg.is_main_template(main):
        errors.append(
            f"addon.template {spec.template!r} is not a known project template; "
            f"choose from {sorted(reg.get_main_templates())}"
        )
        return errors

    steps = _step_templates(main, reg)
    errors += _validate_answers(
        steps, spec.data, config, "addon.data", skip_required=_IMPLICIT_MAIN_ANSWERS
    )

    for i, feat in enumerate(spec.features):
        where = f"features[{i}] ({feat.template})"
        sub = reg.resolve_template_name(feat.template)
        if sub is None:
            errors.append(f"{where}: unknown template {feat.template!r}")
            continue
        valid_sub = any(
            sub in reg._get_subtemplates_for_type(step) for step in steps
        )
        if not valid_sub:
            errors.append(
                f"{where}: not a valid feature for project type(s) "
                f"{sorted(steps)}"
            )
            continue
        errors += _validate_answers(
            [sub],
            feat.data,
            config,
            f"{where}.data",
            skip_required=_IMPLICIT_FEATURE_ANSWERS,
        )

    return errors


def describe_plan(spec: AddonSpec, config: PlonecliConfig) -> str:
    """Render a human-readable summary of what applying the spec would do."""
    reg = TemplateRegistry(config)
    main = reg.resolve_template_name(spec.template) or spec.template
    lines = [f"Plan for {spec.name!r}:", f"  create {main} {spec.name}"]
    if spec.data:
        for key, value in spec.data.items():
            lines.append(f"      -d {key}={value}")
    for feat in spec.features:
        lines.append(f"  add {feat.template}")
        for key, value in feat.data.items():
            lines.append(f"      -d {key}={value}")
    return "\n".join(lines)

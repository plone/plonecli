"""Package name validation for the create command."""

import click
import pytest

from plonecli.cli import _validate_package_name


@pytest.mark.parametrize(
    "name",
    [
        "collective.foo",
        "collective.foo_bar",
        "plone.app.contenttypes",
        "myaddon",
    ],
)
def test_valid_names_pass(name):
    _validate_package_name(name)


@pytest.mark.parametrize(
    "name",
    [
        "collective.new-testcase",
        "my-addon",
        "collective.2foo",
        "collective.class",
        "collective.foo bar",
    ],
)
def test_invalid_names_raise(name):
    with pytest.raises(click.BadParameter):
        _validate_package_name(name)


def test_dash_error_suggests_underscore():
    with pytest.raises(click.BadParameter) as exc:
        _validate_package_name("collective.new-testcase")
    assert "collective.new_testcase" in str(exc.value)


def test_error_names_the_offending_part():
    with pytest.raises(click.BadParameter) as exc:
        _validate_package_name("collective.new-testcase")
    assert "new-testcase" in str(exc.value)


def test_path_is_reduced_to_its_last_component():
    # The create command accepts a target path, not just a bare name.
    _validate_package_name("/tmp/somewhere/collective.foo")


def test_path_with_invalid_last_component_still_raises():
    with pytest.raises(click.BadParameter):
        _validate_package_name("/tmp/somewhere/collective.new-testcase")


def test_no_suggestion_when_underscore_would_not_help():
    with pytest.raises(click.BadParameter) as exc:
        _validate_package_name("collective.2foo")
    assert "Try" not in str(exc.value)


def test_keyword_error_says_keyword_not_identifier():
    # `class` IS a valid identifier -- it is reserved. Saying "not a valid
    # Python identifier" sent the reader looking for a typo that is not there.
    with pytest.raises(click.BadParameter) as exc:
        _validate_package_name("collective.class")
    assert "Python keyword" in str(exc.value)


# ---------------------------------------------------------------------------
# Which templates the check applies to.
#
# NAME is the OUTPUT DIRECTORY (`run_create(target_name=...)`), and only some
# templates turn it into a Python package. Validating it unconditionally
# rejected `plonecli create zope-setup my-project` -- straight out of the
# README -- and broke 26 of the 33 scaffolding evaluations, every one of which
# scaffolds into a hyphenated working directory.
# ---------------------------------------------------------------------------


class _Registry:
    """Minimal stand-in: composite steps only, which is all the helper reads."""

    def __init__(self, steps=None):
        self._steps = steps or []

    def get_composite_steps(self, resolved):
        return self._steps


def _template(tmp_path, name, body):
    d = tmp_path / name
    d.mkdir(parents=True)
    (d / "copier.yml").write_text(body)
    return d


def _config_for(tmp_path, monkeypatch):
    import plonecli.cli as cli

    monkeypatch.setattr(cli, "get_template_path", lambda n, c: tmp_path / n)
    return object()


def test_package_template_is_detected(tmp_path, monkeypatch):
    from plonecli.cli import _template_uses_package_name

    _template(tmp_path, "backend_addon", "package_name:\n  type: str\n")
    cfg = _config_for(tmp_path, monkeypatch)
    assert _template_uses_package_name(_Registry(), cfg, "backend_addon")


def test_project_template_is_not(tmp_path, monkeypatch):
    from plonecli.cli import _template_uses_package_name

    # zope-setup asks project_name, whose value is a directory name.
    _template(tmp_path, "zope-setup", "project_name:\n  type: str\n")
    cfg = _config_for(tmp_path, monkeypatch)
    assert not _template_uses_package_name(_Registry(), cfg, "zope-setup")


def test_composite_is_detected_through_its_steps(tmp_path, monkeypatch):
    from plonecli.cli import _template_uses_package_name

    # `addon` has no copier questions of its own; it composes backend_addon.
    _template(tmp_path, "addon", "_plonecli:\n  type: composite\n")
    _template(tmp_path, "backend_addon", "package_name:\n  type: str\n")
    _template(tmp_path, "zope-setup", "project_name:\n  type: str\n")
    cfg = _config_for(tmp_path, monkeypatch)
    reg = _Registry(["backend_addon", "zope-setup"])
    assert _template_uses_package_name(reg, cfg, "addon")


def test_unreadable_template_does_not_block_scaffolding(tmp_path, monkeypatch):
    from plonecli.cli import _template_uses_package_name

    # Nothing on disk. Refusing to scaffold because a lookup failed would be a
    # worse failure than the one this guard exists to prevent.
    cfg = _config_for(tmp_path, monkeypatch)
    assert not _template_uses_package_name(_Registry(), cfg, "missing")

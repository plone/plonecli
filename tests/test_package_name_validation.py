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

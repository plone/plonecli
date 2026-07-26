"""Pytest configuration for plonecli tests."""

import pytest
from click.testing import CliRunner


@pytest.fixture
def runner():
    return CliRunner()

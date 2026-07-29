"""Tests for plonecli.updater module."""

import json
from datetime import UTC, datetime, timedelta
from unittest.mock import patch

import pytest

from plonecli.updater import (
    _is_newer,
    _read_cache,
    _write_cache,
    check_for_updates,
)


@pytest.mark.parametrize(
    ("latest", "current"),
    [
        ("3.1.0", "3.0.0"),
        ("3.0.0", "2.6.0"),
        # Pre-releases must be comparable, not truncated to their release
        # segment: while plonecli itself ships betas, a newer beta is the only
        # update a user can get.
        ("7.0.0b14", "7.0.0b13"),
        ("7.0.0", "7.0.0b13"),
        ("7.0.0b1", "7.0.0a3"),
        ("7.0.1", "7.0.0"),
        ("7.0.0", "7.0.0.dev0"),
    ],
)
def test_is_newer_true(latest, current):
    assert _is_newer(latest, current) is True


@pytest.mark.parametrize(
    ("latest", "current"),
    [
        ("3.0.0", "3.0.0"),
        ("3.0.0", "3.1.0"),
        ("7.0.0b13", "7.0.0b14"),
        # A final release must never be "updated" to an older pre-release.
        ("7.0.0b13", "7.0.0"),
        ("7.0.0a1", "7.0.0b1"),
        ("7.0.0.dev0", "7.0.0"),
    ],
)
def test_is_newer_false(latest, current):
    assert _is_newer(latest, current) is False


@pytest.mark.parametrize(
    ("latest", "current"),
    [("not-a-version", "3.0.0"), ("3.0.0", "not-a-version")],
)
def test_is_newer_unparseable_never_prompts(latest, current):
    """An unparseable version is not an update; better silent than wrong."""
    assert _is_newer(latest, current) is False


def test_write_and_read_cache(tmp_path, monkeypatch):
    cache_file = tmp_path / ".update_cache.json"
    monkeypatch.setattr("plonecli.updater.UPDATE_CACHE_FILE", cache_file)
    monkeypatch.setattr("plonecli.updater.CONFIG_DIR", tmp_path)

    _write_cache("3.1.0")

    cache = _read_cache()
    assert cache is not None
    assert cache["latest_version"] == "3.1.0"


def test_read_cache_expired(tmp_path, monkeypatch):
    cache_file = tmp_path / ".update_cache.json"
    monkeypatch.setattr("plonecli.updater.UPDATE_CACHE_FILE", cache_file)

    # Write an expired cache
    old_time = (datetime.now(UTC) - timedelta(hours=25)).isoformat()
    cache_file.write_text(
        json.dumps({"last_check": old_time, "latest_version": "3.0.0"})
    )

    cache = _read_cache()
    assert cache is None


def test_read_cache_missing(tmp_path, monkeypatch):
    monkeypatch.setattr("plonecli.updater.UPDATE_CACHE_FILE", tmp_path / "nope.json")
    assert _read_cache() is None


@patch("plonecli.updater._fetch_latest_version", return_value="3.1.0")
@patch("plonecli.updater._get_current_version", return_value="3.0.0")
def test_check_for_updates_new_available(
    mock_current, mock_fetch, tmp_path, monkeypatch
):
    monkeypatch.setattr("plonecli.updater.UPDATE_CACHE_FILE", tmp_path / "cache.json")
    monkeypatch.setattr("plonecli.updater.CONFIG_DIR", tmp_path)

    result = check_for_updates(force=True)
    assert result == "3.1.0"


@patch("plonecli.updater._fetch_latest_version", return_value="7.0.0b14")
@patch("plonecli.updater._get_current_version", return_value="7.0.0b13")
def test_check_for_updates_newer_beta_available(
    mock_current, mock_fetch, tmp_path, monkeypatch
):
    """Beta users must be told about a newer beta."""
    monkeypatch.setattr("plonecli.updater.UPDATE_CACHE_FILE", tmp_path / "cache.json")
    monkeypatch.setattr("plonecli.updater.CONFIG_DIR", tmp_path)

    assert check_for_updates(force=True) == "7.0.0b14"


@patch("plonecli.updater._fetch_latest_version", return_value="3.0.0")
@patch("plonecli.updater._get_current_version", return_value="3.0.0")
def test_check_for_updates_up_to_date(mock_current, mock_fetch, tmp_path, monkeypatch):
    monkeypatch.setattr("plonecli.updater.UPDATE_CACHE_FILE", tmp_path / "cache.json")
    monkeypatch.setattr("plonecli.updater.CONFIG_DIR", tmp_path)

    result = check_for_updates(force=True)
    assert result is None


@patch("plonecli.updater._fetch_latest_version", return_value=None)
@patch("plonecli.updater._get_current_version", return_value="3.0.0")
def test_check_for_updates_network_failure(
    mock_current, mock_fetch, tmp_path, monkeypatch
):
    monkeypatch.setattr("plonecli.updater.UPDATE_CACHE_FILE", tmp_path / "cache.json")
    monkeypatch.setattr("plonecli.updater.CONFIG_DIR", tmp_path)

    result = check_for_updates(force=True)
    assert result is None


@patch("plonecli.updater._get_current_version", return_value="3.0.0")
def test_check_for_updates_uses_cache(mock_current, tmp_path, monkeypatch):
    cache_file = tmp_path / "cache.json"
    monkeypatch.setattr("plonecli.updater.UPDATE_CACHE_FILE", cache_file)
    monkeypatch.setattr("plonecli.updater.CONFIG_DIR", tmp_path)

    # Write a fresh cache with a newer version
    _write_cache("3.2.0")

    # Should use cache, not fetch
    result = check_for_updates(force=False)
    assert result == "3.2.0"

"""Tests for plonecli.updater module."""

import json
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from plonecli.updater import (
    _read_cache,
    _version_tuple,
    _write_cache,
    check_for_updates,
)


def test_version_tuple():
    assert _version_tuple("3.0.0") == (3, 0, 0)
    assert _version_tuple("3.0.0a1") == (3, 0, 0)
    assert _version_tuple("2.6") == (2, 6)
    assert _version_tuple("3.0.0") > _version_tuple("2.6.0")
    assert _version_tuple("3.1.0") > _version_tuple("3.0.0")


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
    old_time = (datetime.now(timezone.utc) - timedelta(hours=25)).isoformat()
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
def test_check_for_updates_new_available(mock_current, mock_fetch, tmp_path, monkeypatch):
    monkeypatch.setattr("plonecli.updater.UPDATE_CACHE_FILE", tmp_path / "cache.json")
    monkeypatch.setattr("plonecli.updater.CONFIG_DIR", tmp_path)

    result = check_for_updates(force=True)
    assert result == "3.1.0"


@patch("plonecli.updater._fetch_latest_version", return_value="3.0.0")
@patch("plonecli.updater._get_current_version", return_value="3.0.0")
def test_check_for_updates_up_to_date(mock_current, mock_fetch, tmp_path, monkeypatch):
    monkeypatch.setattr("plonecli.updater.UPDATE_CACHE_FILE", tmp_path / "cache.json")
    monkeypatch.setattr("plonecli.updater.CONFIG_DIR", tmp_path)

    result = check_for_updates(force=True)
    assert result is None


@patch("plonecli.updater._fetch_latest_version", return_value=None)
@patch("plonecli.updater._get_current_version", return_value="3.0.0")
def test_check_for_updates_network_failure(mock_current, mock_fetch, tmp_path, monkeypatch):
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

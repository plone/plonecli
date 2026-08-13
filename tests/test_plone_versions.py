"""Tests for plonecli.plone_versions: parsing, caching and offline fallback."""

import json
from datetime import UTC, datetime, timedelta
from io import BytesIO
from unittest.mock import patch
from urllib.error import URLError

import pytest

from plonecli.plone_versions import (
    FALLBACK_VERSION,
    _read_cache,
    _write_cache,
    fetch_stable_versions,
    get_latest_stable_version,
    get_version_choices,
)

LISTING = """<html><body>
<a href="../">../</a>
<a href="6.0.13/">6.0.13/</a>
<a href="6.1.0/">6.1.0/</a>
<a href="6.1.1/">6.1.1/</a>
<a href="6.1.2rc1/">6.1.2rc1/</a>
<a href="6.2.0a1/">6.2.0a1/</a>
<a href="6.2.0b2/">6.2.0b2/</a>
<a href="5.2.14/">5.2.14/</a>
<a href="6.1.0.dev0/">6.1.0.dev0/</a>
</body></html>"""


@pytest.fixture
def cache_file(tmp_path, monkeypatch):
    path = tmp_path / ".plone_versions_cache.json"
    monkeypatch.setattr("plonecli.plone_versions.VERSIONS_CACHE_FILE", path)
    monkeypatch.setattr("plonecli.plone_versions.CONFIG_DIR", tmp_path)
    return path


def _urlopen_returning(html):
    return lambda *args, **kwargs: BytesIO(html.encode("utf-8"))


def _offline(*args, **kwargs):
    raise URLError("offline")


def test_fetch_parses_and_sorts_descending():
    with patch("plonecli.plone_versions.urlopen", _urlopen_returning(LISTING)):
        versions = fetch_stable_versions()

    assert versions == ["6.1.1", "6.1.0", "6.0.13", "5.2.14"]


def test_fetch_filters_out_pre_releases():
    with patch("plonecli.plone_versions.urlopen", _urlopen_returning(LISTING)):
        versions = fetch_stable_versions()

    assert not [v for v in versions if any(c.isalpha() for c in v)]


def test_fetch_returns_empty_for_a_listing_without_versions():
    with patch(
        "plonecli.plone_versions.urlopen", _urlopen_returning("<html>nothing</html>")
    ):
        assert fetch_stable_versions() == []


def test_latest_version_is_fetched_and_cached(cache_file):
    with patch("plonecli.plone_versions.urlopen", _urlopen_returning(LISTING)):
        assert get_latest_stable_version(force=True) == "6.1.1"

    cached = json.loads(cache_file.read_text())
    assert cached["latest"] == "6.1.1"
    assert cached["versions"][0] == "6.1.1"


def test_fresh_cache_is_used_without_fetching(cache_file):
    _write_cache(["9.9.9", "9.9.8"], "9.9.9")

    def explode(*args, **kwargs):
        raise AssertionError("network must not be touched with a fresh cache")

    with patch("plonecli.plone_versions.urlopen", explode):
        assert get_latest_stable_version() == "9.9.9"
        assert get_version_choices() == ["9.9.9", "9.9.8"]


def test_expired_cache_triggers_a_refetch(cache_file):
    old = (datetime.now(UTC) - timedelta(hours=25)).isoformat()
    cache_file.write_text(
        json.dumps({"last_check": old, "versions": ["9.9.9"], "latest": "9.9.9"})
    )
    assert _read_cache() is None

    with patch("plonecli.plone_versions.urlopen", _urlopen_returning(LISTING)):
        assert get_latest_stable_version() == "6.1.1"


def test_corrupt_cache_is_ignored(cache_file):
    cache_file.write_text("{not json")

    assert _read_cache() is None

    with patch("plonecli.plone_versions.urlopen", _urlopen_returning(LISTING)):
        assert get_latest_stable_version() == "6.1.1"


def test_offline_falls_back_to_the_stale_cache(cache_file):
    """A stale cache beats the hardcoded fallback when the network is down."""
    old = (datetime.now(UTC) - timedelta(days=30)).isoformat()
    cache_file.write_text(
        json.dumps({"last_check": old, "versions": ["6.0.9"], "latest": "6.0.9"})
    )

    with patch("plonecli.plone_versions.urlopen", _offline):
        assert get_latest_stable_version() == "6.0.9"


def test_offline_without_a_cache_uses_the_fallback(cache_file):
    with patch("plonecli.plone_versions.urlopen", _offline):
        assert get_latest_stable_version() == FALLBACK_VERSION
        assert get_version_choices() == [FALLBACK_VERSION]


def test_version_choices_are_capped_at_five(cache_file):
    listing = "".join(f'<a href="6.1.{n}/">6.1.{n}/</a>' for n in range(10))

    with patch("plonecli.plone_versions.urlopen", _urlopen_returning(listing)):
        choices = get_version_choices(force=True)

    assert len(choices) == 5
    assert choices[0] == "6.1.9"

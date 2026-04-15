"""Fetch and cache available Plone versions from dist.plone.org."""

from __future__ import annotations

import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

from plonecli.config import CONFIG_DIR


PLONE_VERSIONS_URL = "https://dist.plone.org/release/"
VERSIONS_CACHE_FILE = CONFIG_DIR / ".plone_versions_cache.json"
CACHE_MAX_AGE = timedelta(hours=24)
FALLBACK_VERSION = "6.1.1"


def fetch_stable_versions() -> list[str]:
    """Fetch directory listing from dist.plone.org/release/ and return
    stable versions sorted descending (newest first).

    Filters out alpha, beta, rc, and dev releases.
    """
    response = urlopen(PLONE_VERSIONS_URL, timeout=10)  # noqa: S310
    html = response.read().decode("utf-8")

    # Parse directory listing: links like href="6.1.1/"
    version_pattern = re.compile(r'href="(\d+\.\d+[\.\d]*)/?"')
    versions = []
    for match in version_pattern.finditer(html):
        v = match.group(1)
        # Filter: no alpha/beta/rc/dev in the version string
        if not re.search(r"(a|b|rc|dev|alpha|beta)", v, re.IGNORECASE):
            versions.append(v)

    # Sort by version tuple, descending
    versions.sort(
        key=lambda v: tuple(int(x) for x in v.split(".")),
        reverse=True,
    )
    return versions


def _read_cache() -> dict | None:
    """Read the versions cache file. Returns None if missing or expired."""
    if not VERSIONS_CACHE_FILE.exists():
        return None

    try:
        data = json.loads(VERSIONS_CACHE_FILE.read_text())
        last_check = datetime.fromisoformat(data["last_check"])
        if datetime.now(timezone.utc) - last_check > CACHE_MAX_AGE:
            return None
        return data
    except (json.JSONDecodeError, KeyError, ValueError):
        return None


def _write_cache(versions: list[str], latest: str) -> None:
    """Write the versions cache file."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    data = {
        "last_check": datetime.now(timezone.utc).isoformat(),
        "versions": versions,
        "latest": latest,
    }
    VERSIONS_CACHE_FILE.write_text(json.dumps(data))


def get_latest_stable_version(force: bool = False) -> str:
    """Return the latest stable Plone version, cached for 24h.

    Falls back to FALLBACK_VERSION if offline or fetch fails.
    """
    if not force:
        cache = _read_cache()
        if cache:
            return cache.get("latest", FALLBACK_VERSION)

    try:
        versions = fetch_stable_versions()
        if versions:
            latest = versions[0]
            _write_cache(versions, latest)
            return latest
    except (URLError, OSError, TimeoutError):
        pass

    # Try stale cache before falling back
    if VERSIONS_CACHE_FILE.exists():
        try:
            data = json.loads(VERSIONS_CACHE_FILE.read_text())
            return data.get("latest", FALLBACK_VERSION)
        except (json.JSONDecodeError, KeyError):
            pass

    return FALLBACK_VERSION


def get_version_choices(force: bool = False) -> list[str]:
    """Return recent stable versions suitable for template choices.

    Returns up to 5 most recent stable versions, e.g. ['6.1.1', '6.1.0', '6.0.13'].
    """
    if not force:
        cache = _read_cache()
        if cache:
            return cache.get("versions", [FALLBACK_VERSION])[:5]

    try:
        versions = fetch_stable_versions()
        if versions:
            latest = versions[0]
            _write_cache(versions, latest)
            return versions[:5]
    except (URLError, OSError, TimeoutError):
        pass

    return [FALLBACK_VERSION]

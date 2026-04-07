"""Check PyPI for plonecli updates with 24h caching."""

from __future__ import annotations

import importlib.metadata
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

from plonecli.config import CONFIG_DIR


PYPI_URL = "https://pypi.org/pypi/plonecli/json"
UPDATE_CACHE_FILE = CONFIG_DIR / ".update_cache.json"
CACHE_MAX_AGE = timedelta(hours=24)


def _get_current_version() -> str:
    """Get the currently installed plonecli version."""
    return importlib.metadata.version("plonecli")


def _fetch_latest_version() -> str | None:
    """Fetch the latest version from PyPI. Returns None on failure."""
    try:
        response = urlopen(PYPI_URL, timeout=5)  # noqa: S310
        data = json.loads(response.read().decode("utf-8"))
        return data["info"]["version"]
    except (URLError, OSError, TimeoutError, KeyError, json.JSONDecodeError):
        return None


def _read_cache() -> dict | None:
    """Read the update cache. Returns None if missing or expired."""
    if not UPDATE_CACHE_FILE.exists():
        return None

    try:
        data = json.loads(UPDATE_CACHE_FILE.read_text())
        last_check = datetime.fromisoformat(data["last_check"])
        if datetime.now(timezone.utc) - last_check > CACHE_MAX_AGE:
            return None
        return data
    except (json.JSONDecodeError, KeyError, ValueError):
        return None


def _write_cache(latest_version: str) -> None:
    """Write the update cache."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    data = {
        "last_check": datetime.now(timezone.utc).isoformat(),
        "latest_version": latest_version,
    }
    UPDATE_CACHE_FILE.write_text(json.dumps(data))


def _version_tuple(version: str) -> tuple[int, ...]:
    """Parse version string to comparable tuple, ignoring pre-release suffixes."""
    import re

    # Extract just the numeric release segment (e.g. "3.0.0" from "3.0.0a1")
    match = re.match(r"(\d+(?:\.\d+)*)", version)
    if not match:
        return (0,)
    return tuple(int(x) for x in match.group(1).split("."))


def check_for_updates(force: bool = False) -> str | None:
    """Check if a newer version of plonecli is available on PyPI.

    Args:
        force: If True, always fetch from PyPI (ignoring cache).

    Returns:
        The new version string if an update is available, None otherwise.
        Silently returns None on any network/parse error.
    """
    if not force:
        cache = _read_cache()
        if cache:
            latest = cache.get("latest_version")
            if latest:
                current = _get_current_version()
                if _version_tuple(latest) > _version_tuple(current):
                    return latest
            return None

    latest = _fetch_latest_version()
    if latest:
        _write_cache(latest)
        current = _get_current_version()
        if _version_tuple(latest) > _version_tuple(current):
            return latest

    return None

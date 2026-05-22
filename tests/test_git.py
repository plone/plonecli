"""Tests for plonecli.git auto-commit support."""

import subprocess

from plonecli.config import PlonecliConfig
from plonecli.git import commit_template_changes, dirty_files, is_git_repo


def _log(path):
    return subprocess.run(
        ["git", "log", "--pretty=%s"],
        cwd=str(path),
        capture_output=True,
        text=True,
    ).stdout.strip().splitlines()


def test_commit_initializes_repo_and_commits(tmp_path):
    """A fresh package dir gets git init + an initial commit."""
    (tmp_path / "setup.py").write_text("# generated\n")
    config = PlonecliConfig()

    msg = commit_template_changes(
        tmp_path, "backend_addon", config, is_subtemplate=False
    )

    assert msg == "Create package with backend_addon template"
    assert is_git_repo(tmp_path)
    assert _log(tmp_path) == ["Create package with backend_addon template"]


def test_commit_subtemplate_message(tmp_path):
    """Adding a subtemplate to an existing repo uses the 'Add ... subtemplate' message."""
    config = PlonecliConfig()
    (tmp_path / "a.py").write_text("a\n")
    commit_template_changes(tmp_path, "backend_addon", config, is_subtemplate=False)

    (tmp_path / "b.py").write_text("b\n")
    msg = commit_template_changes(tmp_path, "behavior", config, is_subtemplate=True)

    assert msg == "Add behavior subtemplate"
    assert _log(tmp_path) == [
        "Add behavior subtemplate",
        "Create package with backend_addon template",
    ]


def test_commit_noop_when_nothing_changed(tmp_path):
    """A second run with no file changes makes no commit."""
    config = PlonecliConfig()
    (tmp_path / "a.py").write_text("a\n")
    commit_template_changes(tmp_path, "backend_addon", config, is_subtemplate=False)

    msg = commit_template_changes(tmp_path, "behavior", config, is_subtemplate=True)

    assert msg is None
    assert len(_log(tmp_path)) == 1


def test_commit_uses_config_identity_fallback(tmp_path, monkeypatch):
    """When the repo has no git identity, the config author is used."""
    # Isolate from any machine-global git identity so the fallback is exercised.
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(tmp_path / "empty-global"))
    monkeypatch.setenv("GIT_CONFIG_SYSTEM", str(tmp_path / "empty-system"))
    for var in (
        "GIT_AUTHOR_NAME",
        "GIT_AUTHOR_EMAIL",
        "GIT_COMMITTER_NAME",
        "GIT_COMMITTER_EMAIL",
    ):
        monkeypatch.delenv(var, raising=False)

    (tmp_path / "a.py").write_text("a\n")
    subprocess.run(["git", "init"], cwd=str(tmp_path), check=True, capture_output=True)
    # No user.name/user.email configured for this repo.
    config = PlonecliConfig(author_name="Jane Dev", author_email="jane@example.com")

    commit_template_changes(tmp_path, "backend_addon", config, is_subtemplate=False)

    author = subprocess.run(
        ["git", "log", "-1", "--pretty=%an <%ae>"],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
    ).stdout.strip()
    assert author == "Jane Dev <jane@example.com>"


def test_commit_returns_none_for_missing_dir(tmp_path):
    config = PlonecliConfig()
    assert (
        commit_template_changes(
            tmp_path / "nope", "backend_addon", config, is_subtemplate=False
        )
        is None
    )


def test_is_git_repo_false_for_plain_dir(tmp_path):
    assert is_git_repo(tmp_path) is False


def test_dirty_files_clean_or_non_repo(tmp_path):
    # Not a repo at all.
    assert dirty_files(tmp_path) == ([], [])

    # Clean repo after committing everything.
    config = PlonecliConfig()
    (tmp_path / "a.py").write_text("a\n")
    commit_template_changes(tmp_path, "backend_addon", config, is_subtemplate=False)
    assert dirty_files(tmp_path) == ([], [])


def test_dirty_files_reports_modified_and_untracked(tmp_path):
    config = PlonecliConfig()
    (tmp_path / "a.py").write_text("a\n")
    commit_template_changes(tmp_path, "backend_addon", config, is_subtemplate=False)

    (tmp_path / "a.py").write_text("changed\n")
    (tmp_path / "new.py").write_text("new\n")

    modified, untracked = dirty_files(tmp_path)
    assert "a.py" in modified
    assert "new.py" in untracked

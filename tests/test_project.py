"""Tests for plonecli.project module."""

from pathlib import Path

from plonecli.project import find_project_root


def _make_backend_addon(path):
    """Create a minimal backend_addon pyproject.toml."""
    pyproject = path / "pyproject.toml"
    pyproject.write_text("""\
[project]
name = "collective.myaddon"

[tool.plone.backend_addon.settings]
package_name = "collective.myaddon"
package_title = "My Addon"
package_folder = "collective/myaddon"
plone_version = "6.1"
""")


def _make_project(path):
    """Create a minimal zope-setup pyproject.toml."""
    pyproject = path / "pyproject.toml"
    pyproject.write_text("""\
[project]
name = "my-project"

[tool.plone.project.settings]
plone_version = "6.1.1"
distribution = "plone.volto"
db_storage = "instance"
""")


def test_find_backend_addon(tmp_path):
    _make_backend_addon(tmp_path)
    ctx = find_project_root(tmp_path)
    assert ctx is not None
    assert ctx.project_type == "backend_addon"
    assert ctx.package_name == "collective.myaddon"
    assert ctx.package_folder == "collective/myaddon"
    assert ctx.settings["plone_version"] == "6.1"


def test_find_project(tmp_path):
    _make_project(tmp_path)
    ctx = find_project_root(tmp_path)
    assert ctx is not None
    assert ctx.project_type == "zope-setup"
    assert ctx.settings["plone_version"] == "6.1.1"
    assert ctx.settings["distribution"] == "plone.volto"
    assert ctx.settings["project_name"] == "my-project"


def test_find_project_walks_up(tmp_path):
    _make_backend_addon(tmp_path)
    subdir = tmp_path / "src" / "collective" / "myaddon"
    subdir.mkdir(parents=True)
    ctx = find_project_root(subdir)
    assert ctx is not None
    assert ctx.root_folder == tmp_path
    assert ctx.project_type == "backend_addon"


def test_find_project_returns_none(tmp_path):
    ctx = find_project_root(tmp_path)
    assert ctx is None


def test_find_project_ignores_plain_pyproject(tmp_path):
    """A pyproject.toml without [tool.plone.*] sections is not a Plone project."""
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text("""\
[project]
name = "some-random-project"
""")
    ctx = find_project_root(tmp_path)
    assert ctx is None


def test_backend_addon_takes_priority(tmp_path):
    """If both sections exist, backend_addon is detected first."""
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text("""\
[project]
name = "hybrid"

[tool.plone.backend_addon.settings]
package_name = "hybrid"

[tool.plone.project.settings]
plone_version = "6.1"
""")
    ctx = find_project_root(tmp_path)
    assert ctx is not None
    assert ctx.project_type == "backend_addon"


def _make_bobtemplate_cfg(path, template="plone_addon"):
    """Create a legacy bobtemplate.cfg."""
    cfg = path / "bobtemplate.cfg"
    cfg.write_text(f"""\
[main]
version = 5.1
python = python2.7
template = {template}
git_init = y
""")


def test_find_bobtemplate_cfg(tmp_path):
    """A directory with bobtemplate.cfg template=plone_addon is detected as backend_addon."""
    project_dir = tmp_path / "lmu.geozentrum"
    project_dir.mkdir()
    _make_bobtemplate_cfg(project_dir)
    ctx = find_project_root(project_dir)
    assert ctx is not None
    assert ctx.project_type == "backend_addon"
    assert ctx.package_name == "lmu.geozentrum"
    assert ctx.package_folder == "lmu/geozentrum"


def test_bobtemplate_cfg_walks_up(tmp_path):
    """bobtemplate.cfg detection works when starting from a subdirectory."""
    project_dir = tmp_path / "my.addon"
    subdir = project_dir / "src" / "my" / "addon"
    subdir.mkdir(parents=True)
    _make_bobtemplate_cfg(project_dir)
    ctx = find_project_root(subdir)
    assert ctx is not None
    assert ctx.root_folder == project_dir
    assert ctx.project_type == "backend_addon"


def test_pyproject_takes_priority_over_bobtemplate(tmp_path):
    """pyproject.toml detection wins over bobtemplate.cfg."""
    _make_backend_addon(tmp_path)
    _make_bobtemplate_cfg(tmp_path)
    ctx = find_project_root(tmp_path)
    assert ctx is not None
    assert ctx.project_type == "backend_addon"
    assert ctx.package_name == "collective.myaddon"


def test_bobtemplate_cfg_unknown_template_ignored(tmp_path):
    """bobtemplate.cfg with an unknown template type is ignored."""
    _make_bobtemplate_cfg(tmp_path, template="unknown_template")
    ctx = find_project_root(tmp_path)
    assert ctx is None

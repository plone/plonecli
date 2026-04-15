"""Tests for plonecli.registry module."""

from plonecli.config import PlonecliConfig
from plonecli.project import ProjectContext
from plonecli.registry import TemplateRegistry


def _write_template(tmp_path, name, plonecli_meta=None):
    """Create a template directory with a copier.yml.

    If ``plonecli_meta`` is provided it is rendered as the ``_plonecli`` block.
    """
    d = tmp_path / name
    d.mkdir()
    if plonecli_meta is None:
        (d / "copier.yml").write_text(f"# template: {name}\n")
        return

    lines = ["_plonecli:"]
    for key, value in plonecli_meta.items():
        if isinstance(value, list):
            lines.append(f"  {key}:")
            for v in value:
                lines.append(f"    - {v}")
        else:
            lines.append(f"  {key}: {value}")
    (d / "copier.yml").write_text("\n".join(lines) + "\n")


def _setup_templates_dir(tmp_path):
    """Create a mock templates directory mirroring the real metadata schema."""
    _write_template(
        tmp_path,
        "backend_addon",
        {"type": "main", "aliases": ["addon"]},
    )
    _write_template(
        tmp_path,
        "zope-setup",
        {"type": "main", "aliases": ["zope_setup"]},
    )
    _write_template(
        tmp_path,
        "behavior",
        {"type": "sub", "parent": "backend_addon"},
    )
    _write_template(
        tmp_path,
        "content_type",
        {"type": "sub", "parent": "backend_addon"},
    )
    _write_template(
        tmp_path,
        "restapi_service",
        {"type": "sub", "parent": "backend_addon"},
    )
    _write_template(
        tmp_path,
        "zope_instance",
        {"type": "sub", "parent": "zope-setup"},
    )
    return tmp_path


def test_discover_main_templates(tmp_path):
    templates_dir = _setup_templates_dir(tmp_path)
    config = PlonecliConfig(templates_dir=str(templates_dir))
    reg = TemplateRegistry(config)

    main = reg.get_main_templates()
    assert "backend_addon" in main
    assert "zope-setup" in main
    assert "behavior" not in main


def test_discover_subtemplates_for_addon(tmp_path):
    templates_dir = _setup_templates_dir(tmp_path)
    config = PlonecliConfig(templates_dir=str(templates_dir))
    project = ProjectContext(
        root_folder=tmp_path,
        project_type="backend_addon",
        settings={"package_name": "test"},
    )
    reg = TemplateRegistry(config, project)

    subs = reg.get_subtemplates()
    assert "behavior" in subs
    assert "content_type" in subs
    assert "restapi_service" in subs
    assert "zope_instance" not in subs


def test_discover_subtemplates_for_zope_setup(tmp_path):
    templates_dir = _setup_templates_dir(tmp_path)
    config = PlonecliConfig(templates_dir=str(templates_dir))
    project = ProjectContext(
        root_folder=tmp_path,
        project_type="zope-setup",
        settings={"plone_version": "6.1"},
    )
    reg = TemplateRegistry(config, project)

    subs = reg.get_subtemplates()
    assert "zope_instance" in subs
    assert "behavior" not in subs


def test_get_available_templates_outside_project(tmp_path):
    templates_dir = _setup_templates_dir(tmp_path)
    config = PlonecliConfig(templates_dir=str(templates_dir))
    reg = TemplateRegistry(config, project=None)

    available = reg.get_available_templates()
    assert "backend_addon" in available
    assert "zope-setup" in available
    assert "behavior" not in available


def test_get_available_templates_inside_project(tmp_path):
    templates_dir = _setup_templates_dir(tmp_path)
    config = PlonecliConfig(templates_dir=str(templates_dir))
    project = ProjectContext(
        root_folder=tmp_path,
        project_type="backend_addon",
        settings={"package_name": "test"},
    )
    reg = TemplateRegistry(config, project)

    available = reg.get_available_templates()
    assert "behavior" in available
    assert "backend_addon" not in available


def test_list_templates(tmp_path):
    templates_dir = _setup_templates_dir(tmp_path)
    config = PlonecliConfig(templates_dir=str(templates_dir))
    reg = TemplateRegistry(config)

    output = reg.list_templates()
    assert "Available templates:" in output
    assert "backend_addon" in output
    assert "zope-setup" in output


def test_resolve_template_name_alias(tmp_path):
    templates_dir = _setup_templates_dir(tmp_path)
    config = PlonecliConfig(templates_dir=str(templates_dir))
    reg = TemplateRegistry(config)

    assert reg.resolve_template_name("addon") == "backend_addon"
    assert reg.resolve_template_name("backend_addon") == "backend_addon"
    assert reg.resolve_template_name("zope-setup") == "zope-setup"
    assert reg.resolve_template_name("zope_setup") == "zope-setup"


def test_resolve_template_name_unknown(tmp_path):
    templates_dir = _setup_templates_dir(tmp_path)
    config = PlonecliConfig(templates_dir=str(templates_dir))
    reg = TemplateRegistry(config)

    assert reg.resolve_template_name("nonexistent") is None


def test_template_without_metadata_is_ignored(tmp_path):
    """Templates without a _plonecli section should not be listed."""
    _write_template(tmp_path, "backend_addon", {"type": "main"})
    _write_template(tmp_path, "legacy_template")  # no metadata
    config = PlonecliConfig(templates_dir=str(tmp_path))
    reg = TemplateRegistry(config)

    main = reg.get_main_templates()
    assert "backend_addon" in main
    assert "legacy_template" not in main


def test_empty_templates_dir(tmp_path):
    config = PlonecliConfig(templates_dir=str(tmp_path / "nonexistent"))
    reg = TemplateRegistry(config)

    assert reg.get_main_templates() == []
    assert reg.get_subtemplates() == []


def test_subtemplate_with_multiple_parents(tmp_path):
    """A subtemplate may declare multiple parents via a list."""
    _write_template(tmp_path, "backend_addon", {"type": "main"})
    _write_template(tmp_path, "zope-setup", {"type": "main"})
    _write_template(
        tmp_path,
        "shared_thing",
        {"type": "sub", "parent": ["backend_addon", "zope-setup"]},
    )
    config = PlonecliConfig(templates_dir=str(tmp_path))

    addon_proj = ProjectContext(
        root_folder=tmp_path,
        project_type="backend_addon",
        settings={},
    )
    zope_proj = ProjectContext(
        root_folder=tmp_path,
        project_type="zope-setup",
        settings={},
    )

    assert "shared_thing" in TemplateRegistry(config, addon_proj).get_subtemplates()
    assert "shared_thing" in TemplateRegistry(config, zope_proj).get_subtemplates()


def test_is_main_template(tmp_path):
    templates_dir = _setup_templates_dir(tmp_path)
    config = PlonecliConfig(templates_dir=str(templates_dir))
    reg = TemplateRegistry(config)

    assert reg.is_main_template("backend_addon") is True
    assert reg.is_main_template("zope-setup") is True
    assert reg.is_main_template("behavior") is False


def test_is_subtemplate(tmp_path):
    templates_dir = _setup_templates_dir(tmp_path)
    config = PlonecliConfig(templates_dir=str(templates_dir))
    project = ProjectContext(
        root_folder=tmp_path,
        project_type="backend_addon",
        settings={"package_name": "test"},
    )
    reg = TemplateRegistry(config, project)

    assert reg.is_subtemplate("behavior") is True
    assert reg.is_subtemplate("content_type") is True
    assert reg.is_subtemplate("backend_addon") is False

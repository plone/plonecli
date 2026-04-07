"""Tests for plonecli.registry module."""

from plonecli.config import PlonecliConfig
from plonecli.project import ProjectContext
from plonecli.registry import TemplateRegistry


def _setup_templates_dir(tmp_path):
    """Create a mock templates directory with copier.yml files."""
    for name in [
        "backend_addon",
        "zope-setup",
        "behavior",
        "content_type",
        "restapi_service",
        "zope_instance",
    ]:
        d = tmp_path / name
        d.mkdir()
        (d / "copier.yml").write_text(f"# template: {name}\n")
    return tmp_path


def _setup_templates_dir_with_metadata(tmp_path):
    """Create a mock templates directory with _plonecli metadata in copier.yml."""
    # Hardcoded templates (no metadata, rely on fallback)
    for name in ["backend_addon", "zope-setup", "behavior", "content_type"]:
        d = tmp_path / name
        d.mkdir()
        (d / "copier.yml").write_text(f"# template: {name}\n")

    # Self-registering subtemplate
    d = tmp_path / "upgrade_step"
    d.mkdir()
    (d / "copier.yml").write_text(
        "_plonecli:\n"
        "  template_type: sub\n"
        "  parent_types:\n"
        "    - backend_addon\n"
        "  aliases:\n"
        "    - upgrade\n"
    )

    # Self-registering main template
    d = tmp_path / "volto_addon"
    d.mkdir()
    (d / "copier.yml").write_text(
        "_plonecli:\n"
        "  template_type: main\n"
        "  aliases:\n"
        "    - frontend_addon\n"
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


def test_discover_subtemplates_for_project(tmp_path):
    templates_dir = _setup_templates_dir(tmp_path)
    config = PlonecliConfig(templates_dir=str(templates_dir))
    project = ProjectContext(
        root_folder=tmp_path,
        project_type="project",
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


def test_empty_templates_dir(tmp_path):
    config = PlonecliConfig(templates_dir=str(tmp_path / "nonexistent"))
    reg = TemplateRegistry(config)

    assert reg.get_main_templates() == []
    assert reg.get_subtemplates() == []


# --- Dynamic self-registration tests ---


def test_dynamic_main_template(tmp_path):
    """A template with _plonecli.template_type=main is listed as a main template."""
    templates_dir = _setup_templates_dir_with_metadata(tmp_path)
    config = PlonecliConfig(templates_dir=str(templates_dir))
    reg = TemplateRegistry(config)

    main = reg.get_main_templates()
    assert "volto_addon" in main
    assert "backend_addon" in main  # hardcoded fallback still works


def test_dynamic_subtemplate(tmp_path):
    """A template with _plonecli.template_type=sub appears in subtemplates."""
    templates_dir = _setup_templates_dir_with_metadata(tmp_path)
    config = PlonecliConfig(templates_dir=str(templates_dir))
    project = ProjectContext(
        root_folder=tmp_path,
        project_type="backend_addon",
        settings={"package_name": "test"},
    )
    reg = TemplateRegistry(config, project)

    subs = reg.get_subtemplates()
    assert "upgrade_step" in subs
    assert "behavior" in subs  # hardcoded fallback still works


def test_dynamic_subtemplate_wrong_project_type(tmp_path):
    """A dynamic subtemplate only appears for its declared parent_types."""
    templates_dir = _setup_templates_dir_with_metadata(tmp_path)
    config = PlonecliConfig(templates_dir=str(templates_dir))
    project = ProjectContext(
        root_folder=tmp_path,
        project_type="project",
        settings={"plone_version": "6.1"},
    )
    reg = TemplateRegistry(config, project)

    subs = reg.get_subtemplates()
    assert "upgrade_step" not in subs  # only declared for backend_addon


def test_dynamic_alias_resolution(tmp_path):
    """Aliases from _plonecli metadata are resolved correctly."""
    templates_dir = _setup_templates_dir_with_metadata(tmp_path)
    config = PlonecliConfig(templates_dir=str(templates_dir))
    reg = TemplateRegistry(config)

    assert reg.resolve_template_name("upgrade") == "upgrade_step"
    assert reg.resolve_template_name("upgrade_step") == "upgrade_step"
    assert reg.resolve_template_name("frontend_addon") == "volto_addon"
    assert reg.resolve_template_name("volto_addon") == "volto_addon"


def test_is_main_template(tmp_path):
    templates_dir = _setup_templates_dir_with_metadata(tmp_path)
    config = PlonecliConfig(templates_dir=str(templates_dir))
    reg = TemplateRegistry(config)

    assert reg.is_main_template("backend_addon") is True
    assert reg.is_main_template("volto_addon") is True
    assert reg.is_main_template("upgrade_step") is False


def test_is_subtemplate(tmp_path):
    templates_dir = _setup_templates_dir_with_metadata(tmp_path)
    config = PlonecliConfig(templates_dir=str(templates_dir))
    project = ProjectContext(
        root_folder=tmp_path,
        project_type="backend_addon",
        settings={"package_name": "test"},
    )
    reg = TemplateRegistry(config, project)

    assert reg.is_subtemplate("upgrade_step") is True
    assert reg.is_subtemplate("behavior") is True
    assert reg.is_subtemplate("backend_addon") is False


def test_list_templates_shows_dynamic(tmp_path):
    """Dynamic templates appear in list_templates output."""
    templates_dir = _setup_templates_dir_with_metadata(tmp_path)
    config = PlonecliConfig(templates_dir=str(templates_dir))
    reg = TemplateRegistry(config)

    output = reg.list_templates()
    assert "volto_addon" in output
    assert "upgrade_step" in output

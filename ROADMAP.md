# plonecli Roadmap

## Dynamic Template Discovery from `copier.yml`

**Status:** In progress

Replace the hardcoded template lists (`MAIN_TEMPLATES`, `SUBTEMPLATES`, `TEMPLATE_ALIASES` in `templates.py`) with dynamic discovery based on `_plonecli` metadata in each template's `copier.yml`.

### What changes

- The registry scans `copier.yml` files and reads the `_plonecli` metadata section to determine template type (main/sub), parent relationships, aliases, descriptions, and deprecation status.
- Adding a new template to a copier-templates repository requires zero changes to plonecli.
- Templates without a `_plonecli` section are still discovered but won't appear in any listing.

### Files affected

- `plonecli/registry.py` — parse `copier.yml` metadata dynamically
- `plonecli/templates.py` — remove static constants (`MAIN_TEMPLATES`, `SUBTEMPLATES`, `TEMPLATE_ALIASES`, `resolve_template_name()`)
- `plonecli/cli.py` — use registry for all template resolution
- `pyproject.toml` — add `pyyaml` as explicit dependency
- `tests/` — update to use `copier.yml` fixtures with `_plonecli` metadata

See the **Template Registry** section in `README.rst` for the full metadata convention.

---

## Multi-Package Template Support via Entrypoints

**Status:** Planned

Restore the bobtemplates-style multi-package support using modern Python entrypoints, so that multiple installed packages can each provide copier templates to plonecli.

### Entrypoint group: `plonecli.templates`

Template packages register an entrypoint that returns a `Path` to a directory containing copier template subdirectories (each with `copier.yml` + `_plonecli` metadata).

**Template package `pyproject.toml`:**

```toml
[project.entry-points."plonecli.templates"]
plone = "plone_copier_templates:get_templates_dir"
```

**Template package code:**

```python
# plone_copier_templates/__init__.py
from pathlib import Path

def get_templates_dir() -> Path:
    return Path(__file__).parent / "templates"
```

### Registry changes

The registry will scan all registered template directories in addition to the local git clone:

```python
import importlib.metadata

for ep in importlib.metadata.entry_points(group="plonecli.templates"):
    get_dir = ep.load()
    templates_dir = get_dir()
    # scan this dir the same way as the local clone
```

The local git clone remains the default source. Installed packages provide additional sources.

### Conflict resolution

When multiple packages provide templates with the same name:

- Namespace by source: `plone:backend_addon` vs `mycompany:backend_addon`
- Show source package in `plonecli -l` output
- Allow configuration to set priority order

---

## Release `plone-copier-templates` on PyPI

**Status:** Planned (depends on multi-package entrypoint support)

Package the copier-templates repository as `plone-copier-templates` on PyPI, similar to how `bobtemplates.plone` was distributed.

### Goals

- Users can `pip install plone-copier-templates` and templates appear automatically in `plonecli -l`
- Templates are versioned and released alongside plonecli
- Third parties can create and publish their own template packages (e.g. `my-company-plone-templates`)
- The git-clone mechanism remains as a fallback / development workflow

### Package structure

```
plone-copier-templates/
├── pyproject.toml
├── plone_copier_templates/
│   ├── __init__.py          # get_templates_dir() function
│   └── templates/
│       ├── backend_addon/
│       │   └── copier.yml
│       ├── content_type/
│       │   └── copier.yml
│       ├── behavior/
│       │   └── copier.yml
│       └── ...
```

### `pyproject.toml`

```toml
[project]
name = "plone-copier-templates"
version = "1.0.0"
dependencies = []

[project.entry-points."plonecli.templates"]
plone = "plone_copier_templates:get_templates_dir"

[tool.hatch.build.targets.wheel]
packages = ["plone_copier_templates"]
```

---

## Frontend / Volto Template Support

**Status:** Idea

Add support for frontend (Volto) project scaffolding alongside the existing backend templates. This would include templates for Volto add-ons and project setups.

---

## `plonecli update` with Copier Update Support

**Status:** Idea

Integrate copier's built-in update mechanism (`copier update`) so that existing projects can be updated when templates change. This would allow projects created with plonecli to pull in template improvements without recreating from scratch.

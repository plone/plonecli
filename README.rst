.. image:: https://github.com/plone/plonecli/actions/workflows/python-package.yml/badge.svg
    :target: https://github.com/plone/plonecli/actions/workflows/python-package.yml

.. image:: https://img.shields.io/pypi/v/plonecli.svg
    :target: https://pypi.python.org/pypi/plonecli/
    :alt: Latest Version


=========
Plone CLI
=========

.. image:: https://raw.githubusercontent.com/plone/plonecli/master/docs/plone_cli_logo.svg


**A Plone CLI for creating Plone packages**

The Plone CLI is meant for developing Plone packages. It uses `copier <https://copier.readthedocs.io/>`_ templates to scaffold Plone backend addons, Zope project setups, and add features like content types, behaviors, and REST API services.


Installation
============

UV Tool (Recommended)
---------------------

The recommended way to install plonecli is as a UV tool, which makes it available globally:

.. code-block:: shell

    uv tool install plonecli

To upgrade:

.. code-block:: shell

    uv tool upgrade plonecli

Run Without Installing (uvx)
----------------------------

You can run plonecli without installing it using ``uvx``:

.. code-block:: shell

    uvx plonecli create addon my.addon

In a Virtual Environment
------------------------

.. code-block:: shell

    uv venv
    source .venv/bin/activate
    uv pip install plonecli

With pipx
---------

.. code-block:: shell

    pipx install plonecli


First Run
=========

On first run, plonecli will clone the copier-templates repository to ``~/.copier-templates/plone-copier-templates``.

Configure your author defaults:

.. code-block:: shell

    plonecli config

This creates ``~/.plonecli/config.toml`` with your settings.


Usage
=====

Available Commands
------------------

.. code-block:: shell

    plonecli --help

    Commands:
      add      Add features to your existing Plone package
      config   Configure plonecli global settings
      create   Create a new Plone package
      debug    Start the Plone instance in debug mode
      serve    Start the Plone instance
      setup    Run zope-setup inside an existing backend_addon
      test     Run the tests in your package
      update   Update copier-templates and check for plonecli updates

    Options:
      -l, --list-templates   List available templates
      -V, --versions         Show version information
      -h, --help             Show this message and exit.


Creating a Plone Add-on
-----------------------

.. code-block:: shell

    plonecli create addon collective.todo

Or create a Zope project setup:

.. code-block:: shell

    plonecli create zope-setup my-project


Adding Features to Your Plone Add-on
------------------------------------

Inside your addon directory, you can add features through subtemplates:

.. code-block:: shell

    cd collective.todo

    plonecli add content_type
    plonecli add behavior
    plonecli add restapi_service


Setting Up a Zope Project
-------------------------

Inside an existing addon, set up the Zope project infrastructure:

.. code-block:: shell

    cd collective.todo
    plonecli setup


Running Your Application
------------------------

.. code-block:: shell

    plonecli serve

This delegates to ``uv run invoke start`` which is configured by the project templates.


Running Tests
-------------

.. code-block:: shell

    plonecli test

With verbose output:

.. code-block:: shell

    plonecli test --verbose


Debug Mode
----------

.. code-block:: shell

    plonecli debug


Updating Templates
------------------

.. code-block:: shell

    plonecli update

This pulls the latest copier-templates and checks PyPI for plonecli updates.


Listing Templates
-----------------

.. code-block:: shell

    plonecli -l

    Available templates:

      Project templates (plonecli create <template> <name>):
        - backend_addon (alias: addon)
            - behavior
            - content_type
            - restapi_service
        - zope-setup
            - zope_instance

When inside a project, only the applicable subtemplates are shown.


Configuration
=============

Config File
-----------

plonecli stores its configuration at ``~/.plonecli/config.toml``:

.. code-block:: toml

    [author]
    name = "Your Name"
    email = "your@email.com"
    github_user = "yourgithub"

    [defaults]
    plone_version = "6.1.1"

    [templates]
    repo_url = "https://github.com/derico-de/copier-templates"
    branch = "main"
    local_path = "~/.copier-templates/plone-copier-templates"

The default Plone version is fetched from ``https://dist.plone.org/release/`` and cached for 24 hours.

Environment Variables
---------------------

You can override template configuration using environment variables. These take precedence over the config file:

``PLONECLI_TEMPLATES_REPO_URL``
    Override the copier-templates repository URL.

``PLONECLI_TEMPLATES_BRANCH``
    Override the branch to track (default: ``main``).

``PLONECLI_TEMPLATES_DIR``
    Override the local directory for the templates clone.

Example:

.. code-block:: shell

    export PLONECLI_TEMPLATES_REPO_URL=https://github.com/myorg/my-templates
    export PLONECLI_TEMPLATES_BRANCH=develop
    plonecli create addon my.addon

This is useful for:

- Testing custom template forks
- CI/CD environments with pre-cloned templates
- Organizations maintaining their own template sets


Template Registry
=================

plonecli discovers available templates dynamically by scanning for ``copier.yml`` files in the templates directory. Each template must include a ``_plonecli`` metadata section in its ``copier.yml`` so that plonecli knows how to classify and present it.

Metadata Convention
-------------------

Add a ``_plonecli`` key to your template's ``copier.yml``. Copier ignores unknown ``_``-prefixed keys, so this is safe and non-breaking.

**Main template** (used with ``plonecli create``):

.. code-block:: yaml

    # backend_addon/copier.yml
    _plonecli:
      type: main
      aliases:
        - addon
      description: "Create a Plone backend add-on package"

    # ... regular copier questions below ...
    package_name:
      type: str
      help: "Package name (e.g. collective.todo)"

**Subtemplate** (used with ``plonecli add``):

.. code-block:: yaml

    # content_type/copier.yml
    _plonecli:
      type: sub
      parent: backend_addon
      description: "Add a Dexterity content type"

    # ... regular copier questions below ...

Metadata Fields
---------------

``type`` *(required)*
    Either ``main`` or ``sub``.

    - ``main``: A project template, available via ``plonecli create <template> <name>``.
    - ``sub``: A feature template, available via ``plonecli add <template>`` when inside a matching project.

``parent`` *(required for sub, ignored for main)*
    The ``project_type`` of the parent project this subtemplate applies to. This must match the project type that plonecli detects from the project's ``pyproject.toml`` (e.g. ``backend_addon``, ``project``). A subtemplate only appears when you are inside a project of the matching type.

``aliases`` *(optional, default: [])*
    A list of alternative names users can type instead of the directory name. For example, ``aliases: [addon]`` lets users run ``plonecli create addon my.addon`` instead of ``plonecli create backend_addon my.addon``.

``description`` *(optional)*
    A short human-readable description shown in ``plonecli -l`` output.

``deprecated`` *(optional, default: false)*
    Set to ``true`` to mark a template as deprecated. Deprecated templates still work but show a warning.

``info`` *(optional)*
    An informational message displayed when the template is used (e.g. migration instructions for deprecated templates).

How Discovery Works
-------------------

1. plonecli clones the configured copier-templates repository to ``~/.copier-templates/plone-copier-templates`` on first run.
2. The template registry scans each subdirectory for a ``copier.yml`` file.
3. It reads the ``_plonecli`` metadata section from each ``copier.yml``.
4. Templates without a ``_plonecli`` section are still discovered but treated as subtemplates with no parent assignment (they won't appear in any listing).

Template Directory Structure
-----------------------------

A copier-templates repository should follow this layout:

.. code-block:: text

    copier-templates/
    ├── backend_addon/
    │   ├── copier.yml          # Must contain _plonecli metadata
    │   └── {{package_name}}/   # Copier template files
    ├── content_type/
    │   ├── copier.yml
    │   └── ...
    ├── behavior/
    │   ├── copier.yml
    │   └── ...
    └── zope-setup/
        ├── copier.yml
        └── ...

Each subdirectory with a ``copier.yml`` is treated as a template. The directory name is the canonical template name.

Example: Adding a New Template
------------------------------

To add a new subtemplate (e.g. a ``viewlet`` template for backend addons):

1. Create a ``viewlet/`` directory in your copier-templates repository.
2. Add a ``copier.yml`` with the ``_plonecli`` metadata and your copier questions:

   .. code-block:: yaml

       _plonecli:
         type: sub
         parent: backend_addon
         description: "Add a viewlet"

       viewlet_name:
         type: str
         help: "Name of the viewlet"

3. Add your template files (Jinja2 templates rendered by copier).
4. Commit and push. Users pick it up with ``plonecli update``.

No changes to plonecli itself are needed -- the new template is discovered automatically.

Roadmap
-------

See `ROADMAP.md <ROADMAP.md>`_ for planned features including multi-package template support via Python entrypoints and publishing ``plone-copier-templates`` on PyPI.


Developer Guide
===============

Setup Developer Environment
---------------------------

.. code-block:: shell

    git clone https://github.com/plone/plonecli/
    cd plonecli
    uv venv
    uv pip install -e ".[dev,test]"
    uv run plonecli --help
    uv run plonecli -V


Running Tests
-------------

.. code-block:: shell

    # Using tox
    tox

    # Or directly with pytest
    uv run pytest tests/

    # A single test
    uv run pytest tests/ -k test_find_project_root


Contribute
==========

- Issue Tracker: https://github.com/plone/plonecli/issues
- Source Code: https://github.com/plone/plonecli


License
=======

This project is licensed under the BSD license.

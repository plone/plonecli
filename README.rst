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


Developer Guide
===============

Setup Developer Environment
---------------------------

.. code-block:: shell

    git clone https://github.com/plone/plonecli/
    cd plonecli
    uv venv
    uv pip install -e ".[dev,test]"
    plonecli --help


Running Tests
-------------

.. code-block:: shell

    # Using tox
    tox

    # Or directly with pytest
    pytest tests/

    # A single test
    pytest tests/ -k test_find_project_root


Contribute
==========

- Issue Tracker: https://github.com/plone/plonecli/issues
- Source Code: https://github.com/plone/plonecli


License
=======

This project is licensed under the BSD license.

.. image:: https://secure.travis-ci.org/plone/plonecli.png?branch=master
    :target: http://travis-ci.org/plone/plonecli

.. image:: https://coveralls.io/repos/github/plone/plonecli/badge.svg?branch=master
    :target: https://coveralls.io/github/plone/plonecli?branch=master
    :alt: Coveralls

.. image:: https://img.shields.io/pypi/v/plonecli.svg
    :target: https://pypi.python.org/pypi/plonecli/
    :alt: Latest Version

.. image:: https://img.shields.io/pypi/pyversions/bobtemplates.plone.svg?style=plastic
    :alt: PyPI - Python Version

=========
Plone CLI
=========

.. image:: https://github.com/plone/plonecli/blob/master/docs/plone_cli_logo.svg


**A Plone CLI for creating Plone packages**

The Plone CLI is meant for developing Plone packages, we will *not* add functions to install or run Plone in production.
For this we should build another package, let's say ``plonectl`` which will provide installing and deployment functions.

It also support's GIT by default, to keep track of changes one is doing with the templates.


Installation
============

We install plonecli in the global user site-packages, so that we can use it in multiple projects.

**Versions newer than 0.1.1b4 are installable like any other package with pip**.

.. code-block:: shell

    pip install plonecli --user
    plonecli -l

To upgrade plonecli just do:

.. code-block:: shell

    pip install -U plonecli --user

**Note:** Sometimes it happens that you will have older versions of bobtemplates.plone in your system after upgrades.
The best way to solve this is, to uninstall bobtemplates.plone multiple times until it says, that there is no package installed anymore.

Make sure that the install directory is in *$PATH* (e.g. *export PATH=$PATH:$HOME/.local/bin/*)

**Note:** We are now using a the ORIGINAL version of the `CLICK <https://click.palletsprojects.com/>`_ library,
please uninstall plonecli-click before you install the new version of plonecli.

If one would like to use plonecli with pipenv, you can do it as follow:

.. code-block:: shell

    mkdir cli
    cd cli
    pipenv install plonecli
    pipenv shell
    plonecli -l

The same applies if you use other tools like pyenv virtualenv.

NOTE:
When using tools like pyenv or pipenv, you should disable the local virtualenv creation by setting *package.venv.disabled = y* in your .mrbob config file.
You can also use plonecli config to generate the config for you.


Bash Auto Completion
--------------------

To enable auto completion plonecli provides the plonecli_autocomplete.sh script, put the following bash command into your bashrc:

If you installed plonecli in user global packages:

.. code-block:: shell

    . ~/.local/bin/plonecli_autocomplete.sh

If you installed plonecli in a virtualenv it's:

.. code-block:: shell

    . /path/to/your/virtualenv/bin/plonecli_autocomplete.sh


If you used pipenv to install plonecli, you have to find out the path to the virtualenv before:

.. code-block:: shell

    pipenv --virtualenv
    /home/maik/.local/share/virtualenvs/pe-WnXOnVWH
    . /home/maik/.local/share/virtualenvs/pe-WnXOnVWH/bin/plonecli_autocomplete.sh

For other shells than BASH, like Zsh or Fish consult the click-docs:
https://click.palletsprojects.com/en/7.x/bashcomplete/#activation


Documentation
=============

Full documentation for end users can be found in the "docs" folder, this will be available in the Plone docs at some point.

**Note:** you can set default answers for mr.bob questions, see `bobtemplates.plone README <https://github.com/plone/bobtemplates.plone/#configuration>`_.

Details of the templates used by plonecli, you can find in the bobtemplates.plone documentation.
https://bobtemplatesplone.readthedocs.io

Usage
=====

Available Commands
------------------

.. code-block:: shell

    plonecli --help
    Usage: plonecli [OPTIONS] COMMAND1 [ARGS]... [COMMAND2 [ARGS]...]...

      Plone Command Line Interface (CLI)

    Options:
      -l, --list-templates
      -V, --versions
      -h, --help            Show this message and exit.

    Commands:
      build         Bootstrap and build the package
      buildout      Run the package buildout
      config        Configure mr.bob global settings
      create        Create a new Plone package
      debug         Run the Plone client in debug mode
      requirements  Install the local package requirements
      serve         Run the Plone client in foreground mode
      test          Run the tests in your package
      venv          Create/update the local virtual environment...


Creating A Plone Add-on
-----------------------

.. code-block:: console

    $ plonecli -l
    Available mr.bob templates:
     - addon
      - behavior
      - content_type
      - indexer
      - portlet
      - restapi_service
      - subscriber
      - svelte_app
      - theme
      - theme_barceloneta
      - upgrade_step
      - view
      - viewlet
      - vocabulary
      - buildout
    - theme_package [deprecated] >> Please use the theme_barceloneta subtemplate!

    $ plonecli create addon src/collective.todo


Adding Features To Your Plone Add-on
------------------------------------

You can add different features through subtemplates. You can use them also multiple times to create different features of the same type, like two different content types.

.. code-block:: shell

    cd collective.todo

    plonecli add behavior
    plonecli add content_type
    plonecli add theme
    plonecli add view
    plonecli add viewlet
    plonecli add vocabulary


Build Your Package
------------------

.. code-block:: shell

    plonecli build

This will run:

.. code-block:: shell

    python3 -m venv venv
    ./bin/pip install -r requirements.txt --upgrade
    ./bin/buildout bootstrap
    ./bin/buildout

in your target directory.

You can always run the 3 steps explicit by using ``venv``, ``requirements``, ``buildout`` instead of build.
If you want to upgrade/reset your build use the ``--upgrade or --clear`` option on build.

This will clear your virtualenv before installing the requirements and also running buildout with ``-n`` to get the newest versions.


Run Your Application
--------------------

.. code-block:: shell

    plonecli serve


Run Tests for Application
-------------------------

.. code-block:: shell

    plonecli test

or run specific tests:

.. code-block:: shell

    plonecli test -t test_the_thing

or run all tests including Robot tests:

.. code-block:: shell

    plonecli test --all


Combining Commands
------------------

You can combine the steps above like this:

.. code-block:: shell

    plonecli create addon src/collective.todo build test --all serve


Developer Guide
===============

Setup Developer Environment
---------------------------

.. code-block:: shell

    git clone https://github.com/plone/plonecli/
    cd plonecli
    python3 -m venv venv .
    ./venv/bin/pip install -r requirements.txt
    ./venv/bin/pip install -e .[dev,test]
    plonecli --help


Running Tests
-------------

You can run the tests using the following command:

.. code-block:: shell

    tox

or by installing py.test and run the test directly without tox:

.. code-block:: shell

    py.test test/

or a single test:

.. code-block:: shell

    py.test test/ -k test_get_package_root


Register Your Bobtemplates Package For Plonecli
-----------------------------------------------

All mr.bob templates can be registered for plonecli by adding an entry_point to your setup.py.

Here are the entry_points of the bobtemplates.plone package:

.. code-block:: python

    entry_points={
        'mrbob_templates': [
            'plone_addon = bobtemplates.plone.bobregistry:plone_addon',
            'plone_buildout = bobtemplates.plone.bobregistry:plone_buildout',  # NOQA E501
            'plone_theme_package = bobtemplates.plone.bobregistry:plone_theme_package',  # NOQA E501
            'plone_content_type = bobtemplates.plone.bobregistry:plone_content_type',  # NOQA E501
            'plone_view = bobtemplates.plone.bobregistry:plone_view',
            'plone_viewlet = bobtemplates.plone.bobregistry:plone_viewlet',
            'plone_portlet = bobtemplates.plone.bobregistry:plone_portlet',
            'plone_theme = bobtemplates.plone.bobregistry:plone_theme',
            'plone_theme_barceloneta = bobtemplates.plone.bobregistry:plone_theme_barceloneta',  # NOQA E501
            'plone_vocabulary = bobtemplates.plone.bobregistry:plone_vocabulary',  # NOQA E501
            'plone_behavior = bobtemplates.plone.bobregistry:plone_behavior',  # NOQA E501
            'plone_restapi_service = bobtemplates.plone.bobregistry:plone_restapi_service', # NOQA E501
        ],
    },

The entry_point name is used as the global template name for mr.bob.

You also need to provide a bobregistry.py file with a method for each entry_point, it should be named after the entry_point name:

.. code-block:: python

    # -*- coding: utf-8 -*-

    class RegEntry(object):
        def __init__(self):
            self.template = ''
            self.plonecli_alias = ''
            self.depend_on = None
            self.deprecated = False
            self.info = ''


    # standalone template
    def plone_addon():
        reg = RegEntry()
        reg.template = 'bobtemplates.plone:addon'
        reg.plonecli_alias = 'addon'
        return reg


    # sub template
    def plone_theme():
        reg = RegEntry()
        reg.template = 'bobtemplates.plone:theme'
        reg.plonecli_alias = 'theme'
        reg.depend_on = 'plone_addon'
        return reg

For every template you add a line to the entry_points and define a method in the bobregistry.py, which will return a registry object with some properties.

- ``template`` - contains the name of the actual mr.bob template.
- ``plonecli_alias`` - defines the name under which the template will be used inside plonecli
- ``depend_on``:
    1. for a standalone template, the depend_on property is None
    2. for a sub template, the depend_on contains the name of the parent standalone template, usualy `addon`.
- ``deprecated`` - boolean saying whether this templates is deprecated and will be removed in future releases
- ``info`` - message that will be shown next to the template when the template is deprecated


Contribute
==========

- Issue Tracker: https://github.com/plone/plonecli/issues
- Source Code: https://github.com/plone/plonecli


License
=======

This project is licensed under the BSD license.

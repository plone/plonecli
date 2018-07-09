.. image:: https://secure.travis-ci.org/plone/plonecli.png?branch=master
    :target: http://travis-ci.org/plone/plonecli

.. image:: https://coveralls.io/repos/github/plone/plonecli/badge.svg?branch=master
    :target: https://coveralls.io/github/plone/plonecli?branch=master
    :alt: Coveralls

.. image:: https://img.shields.io/pypi/v/plonecli.svg
    :target: https://pypi.python.org/pypi/plonecli/
    :alt: Latest Version

=========
Plone CLI
=========

.. image:: https://github.com/plone/plonecli/blob/master/docs/plone_cli_logo.svg


**A Plone CLI for creating Plone packages**

*The Plone CLI is meant for developing Plone packages, we will not add functions to install or run Plone in production. For this we should build another package, let's say *plonectl* which will provide installing and deployment functions. It also support's GIT by default, to keep track of changes one is doing with the templates.*


Installation
============

We install plonecli in the global user site-packages, so that we can use it in multible projects.

Versions newer than 0.1.1b4 are installable like any other package with pip:

.. code-block:: console

    $ pip install plonecli --user
    $ plonecli -l

To upgrade plonecli just do:

.. code-block:: console

    $ pip install -U plonecli --user


NOTE:
For now we are using a forked version of the click library called plonecli-click.
As soon as the next version of click (>6.7) is out, we will use the normal pypi versions of click.

If would like to use plonecli with pipenv, you can do it as follow:

.. code-block:: console

    $ mkdir cli
    $ cd cli
    $ pipenv install plonecli
    $ pipenv shell
    $ plonecli -l


Bash Auto Completion
--------------------

To enable auto completion plonecli provides the plonecli_autocomplete.sh script, put the following bash command into your bashrc:

If you installed plonecli in user global packages:

.. code-block:: console

    $ . ~/.local/bin/plonecli_autocomplete.sh


If you installed plonecli in a virtualenv it's:

.. code-block:: console

    $ . /path/to/your/virtualenv/bin/plonecli_autocomplete.sh


If you used pipenv to install plonecli, you have to find out the path to the virtualenv before:

.. code-block:: console

    $ pipenv --virtualenv
    /home/maik/.local/share/virtualenvs/pe-WnXOnVWH
    . /home/maik/.local/share/virtualenvs/pe-WnXOnVWH/bin/plonecli_autocomplete.sh


Documentation
=============

Full documentation for end users can be found in the "docs" folder, this will be available in the Plone docs at some point.

*Note:* you can set default answers for mr.bob questions, see `bobtemplates.plone README <https://github.com/plone/bobtemplates.plone/#configuration>`_.

Usage
=====

Available Commands
------------------

.. code-block:: console

    $ plonecli --help
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
      virtualenv    Create/update the local virtual environment...


Creating A Plone Add-on
-----------------------

.. code-block:: console

    $ plonecli -l
    Available mr.bob templates:
     - buildout
     - addon
      - vocabulary
      - theme
      - content_type
     - theme_package

    $ plonecli create addon src/collective.todo


Adding Features To Your Plone Add-on
------------------------------------

.. code-block:: console

    $ cd collective.todo
    $ plonecli -l
    templates:
     - content_type
     - theme
     - vocabulary

    $ plonecli add content_type
    $ plonecli add vocabulary
    $ plonecli add theme


Build Your Package
------------------

.. code-block:: console

    $ plonecli build

This will run:

.. code-block::

    $ virtualenv .
    $ ./bin/pip install -r requirements.txt --upgrade
    $ ./bin/buildout

in your target directory.

You can always run the 3 steps explicit by using ``virtualenv``,``requirements``, ``buildout`` instead of build.
If you want to reset your build use the ``--clean`` option on build.
This will clear your virtualenv before installing the requirements and also running buildout with ``-n`` to get the newest versions.


Run Your Application
--------------------

.. code-block:: console

    $ plonecli serve


Run Tests for Application
-------------------------

.. code-block:: console

    $ plonecli test

or including Robot tests:

.. code-block:: console

    $ plonecli test --all


Combining Commands
------------------

You can combine the steps above like this:

.. code-block:: console

    $ plonecli create addon src/collective.todo build test --all serve


Developer Guide
===============

Setup Developer Environment
---------------------------

.. code-block:: console

    $ git clone https://github.com/plone/plonecli/
    $ cd plonecli
    $ virtualenv .
    $ source bin/activate
    $ pip install -r requirements_dev.txt
    $ python setup.py develop
    $ plonecli --help


Running Tests
-------------

You can run the tests using the following command:

.. code-block:: console

    $ tox

or by installing py.test and run the test directly without tox:

.. code-block:: console

    $ py.test test/

or a single test:

.. code-block:: console

    $ py.test test/ -k test_get_package_root


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
            'plone_theme = bobtemplates.plone.bobregistry:plone_theme',
            'plone_vocabulary = bobtemplates.plone.bobregistry:plone_vocabulary',  # NOQA E501
        ],
    },

The entry_point name is used as the global template name for mr.bob.
You also need to provide the bobregistration.py file with the related methods, which should be named after the entry_point name:

.. code-block:: python

    # -*- coding: utf-8 -*-


    class RegEntry(object):
        def __init__(self):
            self.template = ''
            self.plonecli_alias = ''
            self.depend_on = None


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


Contribute
==========

- Issue Tracker: https://github.com/plone/plonecli/issues
- Source Code: https://github.com/plone/plonecli


License
=======

This project is licensed under the BSD license.

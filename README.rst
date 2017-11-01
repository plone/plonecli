=========
Plone CLI
=========

.. image:: docs/plone_cli_logo.svg

.. image:: https://img.shields.io/pypi/v/plonecli.svg
        :target: https://pypi.python.org/pypi/plonecli

.. image:: https://img.shields.io/travis/MrTango/plonecli.svg
        :target: https://travis-ci.org/MrTango/plonecli

A Plone CLI for creating Plone packages


* Free software: BSD license

Installation
============

.. code-block:: console

    $ easy_install plonecli

NOTE: for now we are using a github version of the click package. As son as the next version (>6.7) is out, we will use the normal pypi versions. This does not work with pip so well, but you can use easy_install for the moment.

Usage
=====

Available commands
------------------

.. code-block:: console

    $ plonecli --help
    Usage: plonecli [OPTIONS] COMMAND1 [ARGS]... [COMMAND2 [ARGS]...]...

      Plone Command Line Interface (CLI)

    Options:
      -l, --list-templates
      --help                Show this message and exit.

    Commands:
      build         Bootstrap and build the package
      buildout      Run the package buildout
      create        Create a new Plone package
      debug         Run the Plone client in debug mode
      requirements  Install the local package requirements
      serve         Run the Plone client in foreground mode
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


Build your package
------------------

.. code-block:: console

    $ plonecli build

This will run:

.. code-block::

    $ virtualenv .
    $ ./bin/pip install -r requirements.txt --upgrade
    $ ./bin/buildout

in you target directory.
You can always run the 3 steps explicit by using ``virtualenv``,``requirements``, ``buildout`` instead of build.
If you want to reset you build use the ``--clean`` option on build. This will clear your virtualenv before installing the requirements and also running buildout with ``-n`` to get the newest versions.


Run your application
--------------------

.. code-block:: console

    $ plonecli serve

Combining commands
------------------

You can combine the steps above like this:

.. code-block:: console

    $ plonecli create addon src/collective.todo build serve


Bash auto completion
--------------------

To enable auto completion plonecli provides the plonecli_autocomplete.sh script, put this into your bashrc:

.. code-block:: console

    $ . /path/to/your/virtualenv/bin/plonecli_autocomplete.sh


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

Register your bobtemplates package for plonecli
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
You also need to provide the bobregistration.py file with the related methods, which should named after the entry_point name:

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
    2. for a sub template, the depend_on contains the name of the parent standalone template.


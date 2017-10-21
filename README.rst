=========
Plone CLI
=========


.. image:: https://img.shields.io/pypi/v/plonecli.svg
        :target: https://pypi.python.org/pypi/plonecli

.. image:: https://img.shields.io/travis/MrTango/plonecli.svg
        :target: https://travis-ci.org/MrTango/plonecli

.. image:: https://readthedocs.org/projects/plonecli/badge/?version=latest
        :target: https://plonecli.readthedocs.io/en/latest/?badge=latest
        :alt: Documentation Status

.. image:: https://pyup.io/repos/github/MrTango/plonecli/shield.svg
     :target: https://pyup.io/repos/github/MrTango/plonecli/
     :alt: Updates


A Plone CLI for creating Plone packages


* Free software: BSD license
* Documentation: https://plonecli.readthedocs.io.


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


Vision
======

Creating A Plone Add-on
-----------------------

.. code-block:: console

    $ pip install plonecli
    $ plonecli -l
    templates:
     - addon
      - content_type
      - theme
      - vocabulary
     - buildout

    $ plonecli create addon collective.todo


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

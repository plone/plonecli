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


Developer guide
===============

Setup developer environment
---------------------------

::

    $ git clone  https://github.com/plone/plonecli/
    $ cd plonecli
    $ virtualenv .
    $ source bin/activate
    $ pip install -r requirements_dev.txt
    $ plonecli --help


Running tests
-------------

Easy as::

    $ tox


Vision
======

creating a Plone addon
......................

.. code-block:: sh

    $ pip install plonecli
    $ plonecli -l
    templates:
     - addon
      - content_type
      - theme
      - vocabulary
     - buildout

    $ plonecli create addon collective.todo

adding features to your Plone addon
...................................

.. code-block:: sh

    $ cd collective.todo
    $ plonecli -l
    templates:
     - content_type
     - theme
     - vocabulary

    $ plonecli add content_type
    $ plonecli add vocabulary
    $ plonecli add theme



Credits
---------

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage


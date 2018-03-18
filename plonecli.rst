========
plonecli
========

During the after conference sprints in Barcelona, we finally created a command line client for developing Plone packages. The plonecli is mainly a wrapper around mr.bob and bobtemplates.plone, but can also used with other bobtemplates. The plonecli forms the previous work on refactoring and modulizing the bobtemplates.plone templates, into a simple and easy to use command line client.

Features
========

- allow bobtemplates to be registered for plonecli
- list available bobtemplates for the current context
- standalone and subtemplates
- auto completion of commands and available templates
- command chaining

Usage
=====

Create a Plone Addon packages
-----------------------------

To create a Plone Addon with the plonecli, you can just use the create command:

.. code-block:: bash

    $ plonecli create addon src/collective.todos

If you want to know what templates are available, you can either use the ``-l/--list-templates`` option or just press TAB-Key twice.

.. code-block:: bash

    $ plonecli --list-templates
    Available mr.bob templates:
     - buildout
     - addon
      - vocabulary
      - theme
      - content_type
     - theme_package

Example
.......

.. image:: docs/plonecli_create_addon_optimized.gif

Add a content_type to your Plone Addon
--------------------------------------

To add a content_type to an existing Plone Addon package, you can just use the add command inside the package:

.. code-block:: bash

    $ cd src/collective.todos
    $ plonecli add content_type

The ``-l/--list-templates`` and auto completion works also for subtemplates (the add command).

.. code-block:: bash

    $ plonecli add
    content_type  theme         vocabulary

.. image:: docs/plonecli_add_content_type_optimized.gif


Add a vocabulary to your Plone Addon
------------------------------------

To add a Plone vocabulary, you can use the add command with the vocabulary subtemplate:

.. code-block:: bash

    $ plonecli add vocabulary

Example
.......

.. image:: docs/plonecli_add_vocabulary_optimized.gif


Build a Plone Addon
-------------------

You can use the plonecli also to build the package:

.. code-block:: bash

    $ plonecli build

This will run:

.. code-block:: bash

    $ virtualenv .
    $ ./bin/pip install -r requirements.txt --upgrade
    $ ./bin/buildout

in your target directory.
You can always run the 3 steps explicit by using the commands ``virtualenv``,``requirements``, ``buildout`` instead of build. If you want to reset your build use the ``--clean`` option on build. This will clear your virtualenv before installing the requirements and also running buildout with ``-n`` to get the newest versions.

Example
.......

.. image:: docs/plonecli_build_optimized.gif


Serve the development Plone site of the package
-----------------------------------------------

The plonecli also provides a serve command which will start the Plone instance in foreground and provide a link to open it in the browser:

.. code-block:: bash

    $ plonecli serve
    RUN: ./bin/instance fg

    INFO: Open this in a Web Browser: http://localhost:8080
    INFO: You can stop it by pressing CTRL + c

    2017-10-30 14:21:01 INFO ZServer HTTP server started at Mon Oct 30 14:21:01 2017
        Hostname: 0.0.0.0
        Port: 8080
    ...

Combine (chain) commands
........................

You can combine commands like create, build and serve:

.. code-block:: bash

    $ plonecli build serve

This will first run all the build steps and then serve the Plone site

Example
.......

.. image:: docs/plonecli_serve_optimized.gif

.. highlight:: shell

============
Installation
============


Stable Release
==============

To install Plone CLI, run this command in your terminal:

.. code-block:: console

    $ pip install plonecli --user

to upgrade, run:

.. code-block:: console

    $ pip install -U plonecli --user

This is the preferred method to install Plone CLI, as it will always install the most recent stable release in the user global site-packages.

If you don't have `pip <https://pip.pypa.io>`_ installed, this `Python installation guide <http://docs.python-guide.org/en/latest/starting/installation/>`_
can guide you through the process.


From Sources
============

The sources for Plone CLI can be downloaded from the `GitHub repo <https://github.com/plone/plonecli/>`_.

You can either clone the public repository:

.. code-block:: console

    $ git clone git@github.com:plone/plonecli.git

Or download the `tarball <https://github.com/plone/plonecli/archive/master.zip>`_:

.. code-block:: console

    $ curl  -OL https://github.com/plone/plonecli/archive/master.zip

Once you have a copy of the source, you can install it with:

.. code-block:: console

    $ python setup.py install

# -*- coding: utf-8 -*-
"""Console script for plonecli."""

import click


@click.group()
def bobtemplates():
    """Support for bobtemplates.plone."""
    pass


@bobtemplates.command()
def create():
    """Create a new Plone package.

    $ mrbob plone_addon -O collective.todo [-v]
    """


@bobtemplates.command()
def add():
    """Add a sub template to your existing package.

    $ mrbob theme [-v]
    """


main = click.CommandCollection(sources=[bobtemplates])


if __name__ == "__main__":
    main()

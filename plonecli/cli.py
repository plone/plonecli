# -*- coding: utf-8 -*-
"""Console script for plonecli."""

import click


@click.group()
def bobtemplates():
    """Support for bobtemplates.plone."""
    pass


@bobtemplates.command()
@click.option('-v', '--verbose', is_flag=True)
def create(verbose):
    """Create a new Plone package."""
    click.echo('create called')
    if verbose:
        click.echo('with verbose param')


@bobtemplates.command()
@click.option('-v', '--verbose', is_flag=True)
def add(verbose):
    """Add a sub template to your existing package."""
    click.echo('add called')
    if verbose:
        click.echo('with verbose param')


@click.group()
def package():
    """Package maintaining group."""
    pass


@package.command('virtualenv')
def create_virtualenv():
    """Create or update the local virtual environment."""
    click.echo('virtualenv called')


@package.command('requirements')
def install_requirements():
    """Install the local package requirements."""
    click.echo('requirements called')


@package.command('build')
def run_buildout():
    """Run the package buildout."""
    click.echo('build called')


@package.command('install')
@click.pass_context
def install_package(ctx):
    """Install the package."""
    ctx.forward(create_virtualenv)
    ctx.forward(install_requirements)
    ctx.forward(run_buildout)


main = click.CommandCollection(sources=[bobtemplates, package])


if __name__ == "__main__":
    main()

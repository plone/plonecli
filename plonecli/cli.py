# -*- coding: utf-8 -*-
"""Console script for plonecli."""

import click


@click.group(chain=True)
def cli():
    """Plone Command Line Interface (CLI)."""
    pass


@cli.command()
@click.option('-v', '--verbose', is_flag=True)
def create(verbose):
    """Create a new Plone package."""
    click.echo('create called')
    if verbose:
        click.echo('with verbose param')


@cli.command()
@click.option('-v', '--verbose', is_flag=True)
def add(verbose):
    """Add a sub template to your existing package."""
    click.echo('add called')
    if verbose:
        click.echo('with verbose param')


@cli.command('virtualenv')
def create_virtualenv():
    """Create or update the local virtual environment."""
    click.echo('virtualenv called')


@cli.command('requirements')
def install_requirements():
    """Install the local package requirements."""
    click.echo('requirements called')


@cli.command('build')
def run_buildout():
    """Run the package buildout."""
    click.echo('build called')


@cli.command('install')
@click.pass_context
def install_package(ctx):
    """Install the package."""
    ctx.forward(create_virtualenv)
    ctx.forward(install_requirements)
    ctx.forward(run_buildout)


main = cli


if __name__ == "__main__":
    main()

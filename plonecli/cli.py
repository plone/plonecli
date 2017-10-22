# -*- coding: utf-8 -*-
"""Console script for plonecli."""

import click


@click.group(chain=True)
def cli():
    """Plone Command Line Interface (CLI)."""
    pass


def get_templates(ctx, args, incomplete):
    """Return a list of available mr.bob templates."""
    return sorted([
        'buildout',
        'theme_package',
        'addon',
    ])


@cli.command()
@click.argument(
    'template',
    type=click.STRING,
    autocompletion=get_templates,
)
@click.argument('name')
@click.option('-v', '--verbose', is_flag=True)
def create(template, name, verbose):
    """Create a new Plone package."""
    click.echo('create called')
    click.echo('template: {0}'.format(template))
    click.echo('package name: {0}'.format(name))
    if verbose:
        click.echo('with verbose param')


def get_subtemplates(ctx, args, incomplete):
    """Return a list of available mr.bob sub-templates."""
    return sorted([
        'sub_template',
        'vocabulary',
        'theme',
    ])


@cli.command()
@click.argument(
    'subtemplate',
    type=click.STRING,
    autocompletion=get_subtemplates,
)
@click.option('-v', '--verbose', is_flag=True)
def add(subtemplate, verbose):
    """Add a sub template to your existing package."""
    click.echo('add called')
    click.echo('sub template: {0}'.format(subtemplate))
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
@click.option('-v', '--verbose', count=True)
def run_buildout(verbose):
    """Run the package buildout."""
    click.echo('build called')
    if verbose:
        click.echo('with verbose param')


@cli.command('install')
@click.option('-v', '--verbose', count=True)
@click.pass_context
def install_package(ctx, verbose):
    """Install the package."""
    ctx.invoke(create_virtualenv)
    ctx.invoke(install_requirements)
    ctx.forward(run_buildout)


main = cli


if __name__ == "__main__":
    main()

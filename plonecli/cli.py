# -*- coding: utf-8 -*-
"""Console script for plonecli."""

import click
import subprocess

from plonecli.registry import TemplateRegistry


@click.group(chain=True)
def cli():
    """Plone Command Line Interface (CLI)."""
    pass


@cli.command()
@click.argument('template')
@click.argument('name')
@click.option('-v', '--verbose', is_flag=True)
def create(template, name, verbose):
    """Create a new Plone package."""
    reg = TemplateRegistry()
    template = reg.resolve_template_name(template)
    if verbose:
        click.echo('RUN: mrbob {0} -O {1}'.format(template, name))
    subprocess.call(
        [
            'mrbob',
            template,
            '-O',
            name,
        ],
    )


@cli.command()
@click.argument('template')
@click.option('-v', '--verbose', is_flag=True)
def add(template, verbose):
    """Add a sub template to your existing package."""
    reg = TemplateRegistry()
    template = reg.resolve_template_name(template)
    if verbose:
        click.echo('RUN: mrbob {0}'.format(template))
    subprocess.call(
        [
            'mrbob',
            template,
        ],
    )


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

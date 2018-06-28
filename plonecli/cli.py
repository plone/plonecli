# -*- coding: utf-8 -*-
"""Console script for plonecli."""

import click
import subprocess
import os

from pkg_resources import WorkingSet
from plonecli.exceptions import NotInPackageError
from plonecli.exceptions import NoSuchValue
from plonecli.registry import template_registry as reg


def echo(msg, fg='green', reverse=False):
    click.echo(
        click.style(msg, fg=fg, reverse=reverse,)
    )


def get_templates(ctx, args, incomplete):
    """Return a list of available mr.bob templates."""
    templates = reg.get_templates()
    return templates


@click.group(
    chain=True,
    context_settings={'help_option_names': ['-h', '--help']},
    invoke_without_command=True
)
@click.option('-l', '--list-templates', 'list_templates', is_flag=True)
@click.option('-V', '--versions', 'versions', is_flag=True)
@click.pass_context
def cli(context, list_templates, versions):
    """Plone Command Line Interface (CLI)"""
    context.obj = {}
    context.obj['target_dir'] = reg.root_folder
    if list_templates:
        click.echo(reg.list_templates())
    if versions:
        ws = WorkingSet()
        bobtemplates_dist = ws.by_key['bobtemplates.plone']
        bobtemplates_version = bobtemplates_dist.version
        plonecli_version = ws.by_key['plonecli'].version
        version_str = """Available packages:\n
        plonecli : {0}\n
        bobtemplates.plone: {1}\n""".format(
                plonecli_version,
                bobtemplates_version,
                )
        click.echo(version_str)


if not reg.root_folder:
    @cli.command()
    @click.argument(
        'template',
        type=click.STRING,
        autocompletion=get_templates,
    )
    @click.argument('name')
    @click.pass_context
    def create(context, template, name):
        """Create a new Plone package"""
        bobtemplate = reg.resolve_template_name(template)
        if bobtemplate is None:
            raise NoSuchValue(
                context.command.name,
                template,
                possibilities=reg.get_templates(),
            )
        cur_dir = os.getcwd()
        context.obj['target_dir'] = '{0}/{1}'.format(cur_dir, name)
        echo(
            '\nRUN: mrbob {0} -O {1}'.format(bobtemplate, name),
            fg='green',
            reverse=True,
        )
        subprocess.call(
            [
                'mrbob',
                bobtemplate,
                '-O',
                name,
            ],
        )

if reg.root_folder:
    @cli.command()
    @click.argument(
        'template',
        type=click.STRING,
        autocompletion=get_templates,
    )
    @click.pass_context
    def add(context, template):
        """Add features to your existing Plone package"""
        if context.obj.get('target_dir', None) is None:
            raise NotInPackageError(context.command.name)
        bobtemplate = reg.resolve_template_name(template)
        if bobtemplate is None:
            raise NoSuchValue(
                context.command.name,
                template,
                possibilities=reg.get_templates(),
            )
        echo(
            '\nRUN: mrbob {0}'.format(bobtemplate),
            fg='green',
            reverse=True,
        )
        subprocess.call(
            [
                'mrbob',
                bobtemplate,
            ],
        )


@cli.command('virtualenv')
@click.option('-c', '--clean', is_flag=True)
@click.pass_context
def create_virtualenv(context, clean):
    """Create/update the local virtual environment for the Plone package"""
    if context.obj.get('target_dir', None) is None:
        raise NotInPackageError(context.command.name)
    params = [
        'virtualenv',
        '.',
    ]
    if clean:
        params.append('--clear')
    echo(
        '\nRUN: {0}'.format(' '.join(params)),
        fg='green',
        reverse=True,
    )
    subprocess.call(
        params,
        cwd=context.obj['target_dir'],
    )


@cli.command('requirements')
@click.pass_context
def install_requirements(context):
    """Install the local package requirements"""

    if context.obj.get('target_dir', None) is None:
        raise NotInPackageError(context.command.name)
    params = [
        './bin/pip',
        'install',
        '-r',
        'requirements.txt',
        '--upgrade',
    ]
    echo(
        '\nRUN: {0}'.format(' '.join(params)),
        fg='green',
        reverse=True,
    )
    subprocess.call(
        params,
        cwd=context.obj['target_dir'],
    )


@cli.command('buildout')
@click.option('-c', '--clean', count=True)
@click.pass_context
def run_buildout(context, clean):
    """Run the package buildout"""
    if context.obj.get('target_dir', None) is None:
        raise NotInPackageError(context.command.name)
    params = [
        './bin/buildout',
    ]
    if clean:
        params.append('-n')
    echo(
        '\nRUN: {0}'.format(' '.join(params)),
        fg='green',
        reverse=True,
    )
    subprocess.call(
        params,
        cwd=context.obj['target_dir'],
    )


@cli.command('serve')
@click.pass_context
def run_serve(context):
    """Run the Plone client in foreground mode"""
    if context.obj.get('target_dir', None) is None:
        raise NotInPackageError(context.command.name)
    params = [
        './bin/instance',
        'fg',
    ]
    echo(
        '\nRUN: {0}'.format(' '.join(params)),
        fg='green',
        reverse=True,
    )
    echo(
        '\nINFO: Open this in a Web Browser: http://localhost:8080',
    )
    echo('INFO: You can stop it by pressing CTRL + c\n')
    subprocess.call(
        params,
        cwd=context.obj['target_dir'],
    )


@cli.command('test')
@click.option('-a', '--all', 'all', is_flag=True)
@click.pass_context
def run_test(context, all):
    """Run the tests in your package"""
    if context.obj.get('target_dir', None) is None:
        raise NotInPackageError(context.command.name)
    params = [
        './bin/test',
    ]
    if all:
        params.append('--all')
    echo(
        '\nRUN: {0}'.format(' '.join(params)),
        fg='green',
        reverse=True,
    )
    subprocess.call(
        params,
        cwd=context.obj['target_dir'],
    )


@cli.command('debug')
@click.pass_context
def run_debug(context):
    """Run the Plone client in debug mode"""
    if context.obj.get('target_dir', None) is None:
        raise NotInPackageError(context.command.name)
    params = [
        './bin/instance',
        'debug',
    ]
    echo(
        '\nRUN: {0}'.format(' '.join(params)),
        fg='green',
        reverse=True,
    )
    echo('INFO: You can stop it by pressing CTRL + c\n')
    subprocess.call(
        params,
        cwd=context.obj['target_dir'],
    )


@cli.command()
@click.option('-c', '--clean', count=True)
@click.pass_context
def build(context, clean):
    """Bootstrap and build the package"""
    target_dir = context.obj.get('target_dir', None)
    if target_dir is None:
        raise NotInPackageError(context.command.name)
    if clean:
        context.invoke(create_virtualenv, clean=True)
    else:
        context.invoke(create_virtualenv)
    context.invoke(install_requirements)
    context.forward(run_buildout)


@cli.command()
def config():
    """Configure mr.bob global settings"""
    echo(
        '\nRUN: mrbob plonecli:configure_mrbob',
        fg='green',
        reverse=True,
    )
    subprocess.call(
        [
            'mrbob',
            'plonecli:configure_mrbob',
        ],
    )


if __name__ == "__main__":
    cli()

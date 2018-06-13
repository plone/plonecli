# -*- coding: utf-8 -*-
"""Configure mrbob."""

from mrbob.bobexceptions import SkipQuestion

import os


try:
    from ConfigParser import ConfigParser
except ImportError:
    from configparser import ConfigParser


home = os.path.expanduser('~')


def generate_answers_ini(path, template):
    with open(os.path.join(path, '.mrbob'), 'w') as f:
        f.write(template)


def check_git_init(configurator, answer):
    if configurator.variables['configure_mrbob.package.git.init']:
        raise SkipQuestion(
            u'GIT is not initialize, so we skip autocommit question.',
        )


def check_mrbob_config(value):
    config = ConfigParser()
    path = home + '/.mrbob'
    config.read(path)
    if not config.sections():
        return
    return config.get('variables', value)


def pre_username(configurator, question):
    """Get username from mrbob config file."""
    default = check_mrbob_config('author.name')
    if default and question:
        question.default = default


def pre_email(configurator, question):
    """Get author email from mrbob config file."""
    default = check_mrbob_config('author.email')
    if default and question:
        question.default = default


def pre_github_username(configurator, question):
    """Get Github username from mrbob config file."""
    default = check_mrbob_config('author.github.user')
    if default and question:
        question.default = default


def pre_plone_version(configurator, question):
    """Get plone version from mrbob config file."""
    default = check_mrbob_config('plone.version')
    if default and question:
        question.default = default


def pre_package_git_init(configurator, question):
    """Get git init setting from mrbob config file."""
    default = check_mrbob_config('package.git.init')
    if default == 'True':
        default = 'y'
    elif default == 'False':
        default = 'n'
    if default and question:
        question.default = default


def pre_package_git_autocommit(configurator, question):
    """Get git autocommit setting from mrbob config file."""
    default = check_mrbob_config('package.git.autocommit')
    if default == 'True':
        default = 'y'
    elif default == 'False':
        default = 'n'
    if default and question:
        question.default = default


def pre_package_git_disable(configurator, question):
    """Get git setting from mrbob config file."""
    default = check_mrbob_config('package.git.disabled')
    if default == 'True':
        default = 'y'
    elif default == 'False':
        default = 'n'
    if default and question:
        question.default = default


def configure(configurator):
    template = """[mr.bob]
verbose = False
[variables]
author.name={0}
author.email={1}
author.github.user={2}
plone.version={3}
package.git.init={4}
package.git.autocommit={5}
package.git.disabled={6}
""".format(
        configurator.variables['configure_mrbob.author.name'],
        configurator.variables['configure_mrbob.author.email'],
        configurator.variables['configure_mrbob.author.github.user'],
        configurator.variables['configure_mrbob.plone.version'],
        configurator.variables['configure_mrbob.package.git.init'],
        configurator.variables['configure_mrbob.package.git.autocommit'],
        configurator.variables['configure_mrbob.package.git.disabled'],
    )
    generate_answers_ini(home, template)

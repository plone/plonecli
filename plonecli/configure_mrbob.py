# -*- coding: utf-8 -*-
"""Configure mrbob."""
from __future__ import absolute_import
from bobtemplates.plone.base import echo
from mrbob.configurator import SkipQuestion

import codecs
import os


try:
    from six.moves.configparser import RawConfigParser
except ImportError:
    from configparser import RawConfigParser

home_path = os.path.expanduser('~')


def check_git_disabled(configurator, answer):
    if configurator.variables['configure_mrbob.package.git.disabled']:
        raise SkipQuestion(
            u'GIT is disabled, so we skip git related questions.',
        )


def get_mrbob_config_variable(varname, dirname):
    """Checks mrbob config of given variable from ~/.mrbob file """
    config = RawConfigParser()
    file_name = '.mrbob'
    config_path = dirname + '/' + file_name
    file_list = os.listdir(dirname)
    if file_name not in file_list:
        return
    config.readfp(codecs.open(config_path, 'r', 'utf-8'))
    if not config.sections():
        return
    if config.has_option('variables', varname):
        return config.get('variables', varname)
    else:
        return


def pre_username(configurator, question):
    """Get username from mrbob config file."""
    default = get_mrbob_config_variable('author.name', home_path)
    if default and question:
        question.default = default


def pre_email(configurator, question):
    """Get author email from mrbob config file."""
    default = get_mrbob_config_variable('author.email', home_path)
    if default and question:
        question.default = default


def pre_github_username(configurator, question):
    """Get Github username from mrbob config file."""
    default = get_mrbob_config_variable('author.github.user', home_path)
    if default and question:
        question.default = default


def pre_plone_version(configurator, question):
    """Get plone version from mrbob config file."""
    default = get_mrbob_config_variable('plone.version', home_path)
    if default and question:
        question.default = default


def pre_package_git_init(configurator, question):
    """Get git init setting from mrbob config file."""
    default = get_mrbob_config_variable('package.git.init', home_path)
    if default and question:
        question.default = default


def pre_package_git_autocommit(configurator, question):
    """Get git autocommit setting from mrbob config file."""
    default = get_mrbob_config_variable('package.git.autocommit', home_path)
    if default and question:
        question.default = default


def pre_package_git_disable(configurator, question):
    """Get git setting from mrbob config file."""
    default = get_mrbob_config_variable('package.git.disabled', home_path)
    if default and question:
        question.default = default


def generate_mrbob_ini(configurator, directory_path, answers):
    file_name = u'.mrbob'
    file_path = directory_path + '/' + file_name
    file_list = os.listdir(directory_path)
    if file_name not in file_list:
        template = """[mr.bob]
verbose = False
[variables]
author.name={0}
author.email={1}
author.github.user={2}
plone.version={3}
""".format(
            answers['author.name'],
            answers['author.email'],
            answers['author.github.user'],
            answers['plone.version'],
        )
        if configurator.variables['configure_mrbob.package.git.disabled']:
            template = template + 'package.git.disabled={0}'.format(
                answers['package.git.disabled'],
            )
        if not configurator.variables['configure_mrbob.package.git.disabled']:
            template = template + """package.git.disabled={0}
package.git.init={1}
package.git.autocommit={2}
""".format(
                answers['package.git.disabled'],
                answers['package.git.init'],
                answers['package.git.autocommit'],
            )

        with open(file_path, 'w') as f:
            f.write(template)
    else:
        # get config file contents
        lines = [line.rstrip('\n') for line in codecs.open(file_path, 'r', 'utf-8')]   # NOQA: E501
        commented_settings = [line for line in lines if line and line[0] == '#']    # NOQA: E501
        config = RawConfigParser()
        # to explicitly convert `key` to str so that we don't get error in
        # .join() of `value`(of type str) and `key`(of type unicode)
        # in RawConfigParser.write() method
        config.optionxform = str
        config.readfp(codecs.open(file_path, 'r', 'utf-8'))
        if not config.has_section('variables'):
            config.add_section('variables')
        for key, value in answers.items():
            config.set('variables', key, value)
        with open(file_path, 'w') as mrbob_config_file:
            config.write(mrbob_config_file)
        # append commented settings at the end
        with codecs.open(file_path, 'a', 'utf-8') as mrbob_config_file:
            mrbob_config_file.writelines(commented_settings)


def post_render(configurator, target_directory=None):
    mrbob_config = {}
    mrbob_config['author.name'] = \
        configurator.variables['configure_mrbob.author.name'].encode('utf-8')
    mrbob_config['author.email'] = \
        configurator.variables['configure_mrbob.author.email'].encode('utf-8')
    mrbob_config['author.github.user'] = \
        configurator.variables['configure_mrbob.author.github.user'].encode('utf-8')  # NOQA: E501
    if not configurator.variables['configure_mrbob.package.git.disabled']:
        mrbob_config['package.git.disabled'] = 'n'
        mrbob_config['package.git.init'] = \
            configurator.variables['configure_mrbob.package.git.init']
        mrbob_config['package.git.autocommit'] = \
            configurator.variables['configure_mrbob.package.git.autocommit']
    else:
        mrbob_config['package.git.disabled'] = 'y'
    mrbob_config['plone.version'] = \
        configurator.variables['configure_mrbob.plone.version'].encode('utf-8')
    if not target_directory:
        configurator.target_directory = home_path
        target_directory = configurator.target_directory
    generate_mrbob_ini(configurator, target_directory, mrbob_config)
    echo(
        u'\nMrbob\'s settings have been saved to {0}/.mrbob\n'.format(
            target_directory,
        ),
        msg_type='info',
    )

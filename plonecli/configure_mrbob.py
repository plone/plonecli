# -*- coding: utf-8 -*-
"""Configure mrbob."""

from mrbob.bobexceptions import SkipQuestion
from bobtemplates.plone.base import get_git_info

import os


home = os.path.expanduser('~')


def generate_answers_ini(path, template):
    with open(os.path.join(path, '.mrbob'), 'w') as f:
        f.write(template)


def pre_username(configurator, question):
    """Get email from git and validate package name."""
    default = get_git_info('user.name')
    if default and question:
        question.default = default


def check_git_init(configurator, answer):
    if configurator.variables['configure_mrbob.package.git.init']:
        raise SkipQuestion(
            u'GIT is not initialize, so we skip autocommit question.',
        )


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

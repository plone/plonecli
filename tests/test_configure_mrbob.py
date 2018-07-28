# -*- coding: utf-8 -*-

from mrbob.bobexceptions import ValidationError
from mrbob.configurator import Configurator
from mrbob.configurator import Question
from mrbob.configurator import SkipQuestion
from plonecli.configure_mrbob import check_git_disabled
from plonecli.configure_mrbob import get_mrbob_config_variable
from plonecli.configure_mrbob import post_render

import os.path
import pytest


def generate_answers_ini(path, template, filename):
    with open(os.path.join(path, filename), 'w') as f:
        f.write(template)


def test_check_git_disabled_true(tmpdir):
    configurator = Configurator(
        template='plonecli:configure_mrbob',
        target_directory=tmpdir.strpath,
        bobconfig={
            'non_interactive': True,
        },
        variables={
            'configure_mrbob.author.name': 'The Plone Collective',
            'configure_mrbob.author.email': 'collective@plone.org',
            'configure_mrbob.author.github.user': 'collective',
            'configure_mrbob.package.git.disabled': True,
        },
    )
    with pytest.raises(SkipQuestion):
        check_git_disabled(configurator, None)


def test_check_git_disabled_false(tmpdir):
    configurator = Configurator(
        template='plonecli:configure_mrbob',
        target_directory=tmpdir.strpath,
        bobconfig={
            'non_interactive': True,
        },
        variables={
            'configure_mrbob.author.name': 'The Plone Collective',
            'configure_mrbob.author.email': 'collective@plone.org',
            'configure_mrbob.author.github.user': 'collective',
            'configure_mrbob.package.git.disabled': False,
            'configure_mrbob.package.git.init': True,
            'configure_mrbob.package.git.autocommit': True,
            'configure_mrbob.plone.version': '5.1',
        },
    )
    check_git_disabled(configurator, None)


def test_get_mrbob_config_variable(tmpdir):
    # when .mrbob file does not exists
    assert get_mrbob_config_variable('author.name', tmpdir.strpath) == None
    assert get_mrbob_config_variable('author.email', tmpdir.strpath) == None
    assert get_mrbob_config_variable('author.github.user', tmpdir.strpath) == None
    assert get_mrbob_config_variable('package.git.init', tmpdir.strpath) == None
    assert get_mrbob_config_variable('package.git.autocommit', tmpdir.strpath) == None
    assert get_mrbob_config_variable('package.git.disabled', tmpdir.strpath) == None
    assert get_mrbob_config_variable('plone.version', tmpdir.strpath) == None
    # when .mrbob file exists but without variable section
    assert get_mrbob_config_variable('author.name', tmpdir.strpath) == None
    assert get_mrbob_config_variable('author.email', tmpdir.strpath) == None
    assert get_mrbob_config_variable('author.github.user', tmpdir.strpath) == None
    assert get_mrbob_config_variable('package.git.init', tmpdir.strpath) == None
    assert get_mrbob_config_variable('package.git.autocommit', tmpdir.strpath) == None
    assert get_mrbob_config_variable('package.git.disabled', tmpdir.strpath) == None
    assert get_mrbob_config_variable('plone.version', tmpdir.strpath) == None
    # when .mrbob file exists with variable section
    template = """[mr.bob]
verbose = False
[variables]
author.name = The Plone Collective
author.email = collective@plone.org
author.github.user = collective
package.git.init = y
package.git.autocommit = y
package.git.disabled = n
plone.version = 5.1
"""
    with open(os.path.join(tmpdir.strpath, '.mrbob'), 'w') as f:
        f.write(template)
    # when .mrbob file exists with git.disabled set to False
    assert get_mrbob_config_variable('author.name', tmpdir.strpath) == 'The Plone Collective'
    assert get_mrbob_config_variable('author.email', tmpdir.strpath) == 'collective@plone.org'
    assert get_mrbob_config_variable('author.github.user', tmpdir.strpath) == 'collective'
    assert get_mrbob_config_variable('package.git.init', tmpdir.strpath) == 'y'
    assert get_mrbob_config_variable('package.git.autocommit', tmpdir.strpath) == 'y'
    assert get_mrbob_config_variable('package.git.disabled', tmpdir.strpath) == 'n'
    assert get_mrbob_config_variable('plone.version', tmpdir.strpath) == '5.1'
    # when .mrbob file exists with git.disabled set to True
    template = """[mr.bob]
verbose = False
[variables]
author.name = The Plone Collective
author.email = collective@plone.org
author.github.user = collective
package.git.disabled = y
plone.version = 5.1
"""
    with open(os.path.join(tmpdir.strpath, '.mrbob'), 'w') as f:
        f.write(template)
    assert get_mrbob_config_variable('author.name', tmpdir.strpath) == 'The Plone Collective'
    assert get_mrbob_config_variable('author.email', tmpdir.strpath) == 'collective@plone.org'
    assert get_mrbob_config_variable('author.github.user', tmpdir.strpath) == 'collective'
    assert get_mrbob_config_variable('package.git.init', tmpdir.strpath) == None
    assert get_mrbob_config_variable('package.git.autocommit', tmpdir.strpath) == None
    assert get_mrbob_config_variable('package.git.disabled', tmpdir.strpath) == 'y'
    assert get_mrbob_config_variable('plone.version', tmpdir.strpath) == '5.1'


def test_plonecli_config_without_config_file(tmpdir):
    configurator = Configurator(
        template='plonecli:configure_mrbob',
        target_directory=tmpdir.strpath,
        bobconfig={
            'non_interactive': True,
        },
        variables={
            'configure_mrbob.author.name': 'The Plone Collective',
            'configure_mrbob.author.email': 'collective@plone.org',
            'configure_mrbob.author.github.user': 'collective',
            'configure_mrbob.package.git.init': 'y',
            'configure_mrbob.package.git.autocommit': 'y',
            'configure_mrbob.package.git.disabled': 'y',
            'configure_mrbob.plone.version': '5.1',
        },
    )
    post_render(configurator, target_directory=tmpdir.strpath)
    template = """[mr.bob]
verbose = False
[variables]
author.name = The Plone Collective
author.email = collective@plone.org
author.github.user = collective
package.git.init = y
package.git.autocommit = y
package.git.disabled = y
plone.version = 5.1
"""
    with open(os.path.join(tmpdir.strpath, '.mrbob'), 'r') as f:
        content = f.read()
        assert content != template


def test_plonecli_config_with_config_file(tmpdir):
    template = """[mr.bob]
verbose = False
[variables]
author.name = The Plone Collective
author.email = collective@plone.org
author.github.user = collective
package.git.init = y
package.git.autocommit = y
package.git.disabled = y
plone.version = 5.1
"""
    with open(os.path.join(tmpdir.strpath, '.mrbob'), 'w') as f:
        f.write(template)

    configurator = Configurator(
        template='plonecli:configure_mrbob',
        target_directory=tmpdir.strpath,
        bobconfig={
            'non_interactive': True,
        },
        variables={
            'configure_mrbob.author.name': 'XYZ',
            'configure_mrbob.author.email': 'collective@plone.org',
            'configure_mrbob.author.github.user': 'collective',
            'configure_mrbob.package.git.init': 'y',
            'configure_mrbob.package.git.autocommit': 'y',
            'configure_mrbob.package.git.disabled': 'y',
            'configure_mrbob.plone.version': '5.1',
        },
    )
    post_render(configurator, target_directory=tmpdir.strpath)
    with open(os.path.join(tmpdir.strpath, '.mrbob'), 'r') as f:
        content = f.read()
        assert 'XYZ' in content


def test_plonecli_config_with_comments(tmpdir):
    template = """[mr.bob]
verbose = False
[variables]
author.name = The Plone Collective
author.email = collective@plone.org
#author.github.user = collective
package.git.init = y
package.git.autocommit = y
package.git.disabled = y
plone.version = 5.1
"""
    with open(os.path.join(tmpdir.strpath, '.mrbob'), 'w') as f:
        f.write(template)

    configurator = Configurator(
        template='plonecli:configure_mrbob',
        target_directory=tmpdir.strpath,
        bobconfig={
            'non_interactive': True,
        },
        variables={
            'configure_mrbob.author.name': 'XYZ',
            'configure_mrbob.author.email': 'collective@plone.org',
            'configure_mrbob.author.github.user': 'collective',
            'configure_mrbob.package.git.init': 'y',
            'configure_mrbob.package.git.autocommit': 'y',
            'configure_mrbob.package.git.disabled': 'y',
            'configure_mrbob.plone.version': '5.1',
        },
    )
    post_render(configurator, target_directory=tmpdir.strpath)
    with open(os.path.join(tmpdir.strpath, '.mrbob'), 'r') as f:
        content = f.read()
        assert '#author.github.user' in content


def test_plonecli_config_with_other_tags(tmpdir):
    template = """[mr.bob]
verbose = False
[defaults]
author.age = 21
[variables]
author.name = The Plone Collective
author.email = collective@plone.org
author.github.user = collective
package.git.disabled = y
plone.version = 5.1
"""
    with open(os.path.join(tmpdir.strpath, '.mrbob'), 'w') as f:
        f.write(template)

    configurator = Configurator(
        template='plonecli:configure_mrbob',
        target_directory=tmpdir.strpath,
        bobconfig={
            'non_interactive': True,
        },
        variables={
            'configure_mrbob.author.name': 'XYZ',
            'configure_mrbob.author.email': 'collective@plone.org',
            'configure_mrbob.author.github.user': 'collective',
            'configure_mrbob.package.git.init': 'y',
            'configure_mrbob.package.git.autocommit': 'y',
            'configure_mrbob.package.git.disabled': 'n',
            'configure_mrbob.plone.version': '5.1',
        },
    )
    post_render(configurator, target_directory=tmpdir.strpath)
    with open(os.path.join(tmpdir.strpath, '.mrbob'), 'r') as f:
        content = f.read()
        assert '[defaults]' in content
        assert 'author.age' in content

#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `plonecli` package."""
import os

from plonecli.registry import template_registry as reg


def test_list_templates(tmpdir):
    os.chdir(tmpdir.strpath)
    template_str = reg.list_templates()
    assert '- buildout' in template_str
    assert '- addon' in template_str
    assert '- theme' in template_str
    assert '- content_type' in template_str


def test_get_subtemplates(tmpdir):
    """ test get_templates inside of a package
    """
    template = """[check-manifest]
check=True

[tool:bobtemplates.plone]
template=plone_addon
"""
    target_dir = tmpdir.strpath + '/collective.foo'
    os.mkdir(target_dir)
    with open(os.path.join(target_dir + '/setup.cfg'), 'w') as f:
        f.write(template)
    with open(os.path.join(target_dir + '/setup.py'), 'w') as f:
        f.write("#")
    os.chdir(target_dir)
    templates = reg.get_templates()
    assert 'content_type' in templates
    assert 'theme' in templates
    assert 'vocabulary' in templates


def test_get_templates(tmpdir):
    """ test get_templates outside of a package
    """
    os.chdir(tmpdir.strpath)
    templates = reg.get_templates()
    assert 'addon' in templates
    assert 'theme_package' in templates
    assert 'buildout' in templates


def test_resolve_template_name(tmpdir):
    """ test resolving template names from plonecli alias
    """
    plonecli_alias = 'addon'
    template_name = reg.resolve_template_name(plonecli_alias)
    assert 'bobtemplates.plone:addon' == template_name

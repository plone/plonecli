#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `plonecli` package."""
import os

from plonecli.registry import TemplateRegistry
from plonecli.registry import get_package_root


def test_list_templates(tmpdir):
    os.chdir(tmpdir.strpath)
    reg = TemplateRegistry()
    template_str = reg.list_templates()
    assert '- buildout' in template_str
    assert '- addon' in template_str
    assert '- theme' in template_str
    assert '- content_type' in template_str


def test_get_package_root(tmpdir):
    target_dir = tmpdir.strpath + '/collective.foo'
    os.mkdir(target_dir)

    package_root = get_package_root()
    assert package_root is None

    os.chdir(target_dir)
    template = """[check-manifest]
check=True

"""
    with open(os.path.join(target_dir + '/bobtemplate.cfg'), 'w') as f:
        f.write(template)

    package_root = get_package_root()
    assert package_root is None

    # test with correct bobtemplate.cfg:
    template = """[check-manifest]
check=True

[main]
template=plone_addon
version=5.1-latest
"""
    with open(os.path.join(target_dir + '/bobtemplate.cfg'), 'w') as f:
        f.write(template)

    package_root = get_package_root()
    assert package_root is not None


def test_get_subtemplates(tmpdir):
    """ test get_templates inside of a package
    """
    template = """[check-manifest]
check=True

[main]
template=plone_addon
version=5.1-latest
"""
    target_dir = tmpdir.strpath + '/collective.foo'
    os.mkdir(target_dir)
    with open(os.path.join(target_dir + '/bobtemplate.cfg'), 'w') as f:
        f.write(template)
    os.chdir(target_dir)
    reg = TemplateRegistry()
    templates = reg.get_templates()
    assert 'content_type' in templates
    assert 'theme' in templates
    assert 'vocabulary' in templates


def test_get_templates(tmpdir):
    """ test get_templates outside of a package
    """
    os.chdir(tmpdir.strpath)
    reg = TemplateRegistry()
    templates = reg.get_templates()
    assert 'addon' in templates
    assert 'theme_package' in templates
    assert 'buildout' in templates


def test_resolve_template_name(tmpdir):
    """ test resolving template names from plonecli alias
    """
    plonecli_alias = 'addon'
    reg = TemplateRegistry()
    template_name = reg.resolve_template_name(plonecli_alias)
    assert 'bobtemplates.plone:addon' == template_name

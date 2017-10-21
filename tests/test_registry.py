#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `plonecli` package."""
import os

from plonecli.registry import TemplateRegistry


def test_get_templates(tmpdir):
    """
    """
    template = """[check-manifest]
check=True

[tool:bobtemplates.plone]
template='addon'
"""
    target_dir = tmpdir.strpath + '/collective.foo'
    os.mkdir(target_dir)
    with open(os.path.join(target_dir + '/setup.cfg'), 'w') as f:
        f.write(template)
    with open(os.path.join(target_dir + '/setup.py'), 'w') as f:
        f.write("#")
    os.chdir(target_dir)
    reg = TemplateRegistry()
    templates = reg.get_templates()

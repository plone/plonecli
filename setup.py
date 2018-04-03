#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The setup script."""
from setuptools import find_packages
from setuptools import setup

test_requirements = [
    'pytest',
]

setup(
    # metadata see setup.cfg
    packages=find_packages(include=['plonecli']),
    entry_points={
        'console_scripts': [
            'plonecli=plonecli.cli:cli'
        ]
    },
    include_package_data=True,
    install_requires=[
        'setuptools',
        'virtualenv',
        # 'Click>=6.8a99',
        'plonecli-click',
        'mr.bob',
        'zest.releaser',
        'bobtemplates.plone>=3.1.1',
    ],
    extras_require={
        'test': test_requirements,
        'dev': [
            'tox',
            'zest.releaser[recommended]',
        ],
    },
    zip_safe=False,
    keywords='plonecli',
    scripts=['plonecli_autocomplete.sh'],
    test_suite='tests',
    tests_require=test_requirements,
    setup_requires=['pytest-runner'],
)

#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The setup script."""

from setuptools import setup, find_packages

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

requirements = [
    'Click>=6.8a99',
    'bobtemplates.plone>=3.0.0a3',
    'mr.bob',
    'zest.releaser',
    # TODO: put package requirements here
]

setup_requirements = [
    'pytest-runner',
    # TODO(MrTango): put setup requirements (distutils extensions, etc.) here
]

test_requirements = [
    'pytest',
    # TODO: put package test requirements here
]

setup(
    name='plonecli',
    version='0.1.0a4.dev0',
    description="A Plone CLI for creating Plone packages",
    long_description=readme + '\n\n' + history,
    author="Maik Derstappen",
    author_email='md@derico.de',
    url='https://github.com/MrTango/plonecli',
    packages=find_packages(include=['plonecli']),
    entry_points={
        'console_scripts': [
            'plonecli=plonecli.cli:cli'
        ]
    },
    include_package_data=True,
    install_requires=requirements,
    dependency_links=['https://github.com/MrTango/click/tarball/plonecli_010#egg=click-6.8a99'],  # NOQA E501
    license="BSD license",
    zip_safe=False,
    keywords='plonecli',
    scripts=['plonecli_autocomplete.sh'],
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
    test_suite='tests',
    tests_require=test_requirements,
    setup_requires=setup_requirements,
)

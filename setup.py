#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Setup file for Cloudcrane
"""

import sys
import os
import inspect

import setuptools
from setuptools.command.test import test as TestCommand
from setuptools import setup

if sys.version_info < (3, 6, 0):
    sys.stderr.write('FATAL: Cloudcrane needs to be run with Python 3.6+\n')
    sys.exit(1)
__location__ = os.path.join(os.getcwd(), os.path.dirname(inspect.getfile(inspect.currentframe())))


def read_version(package):
    data = {}
    with open(os.path.join(package, '__init__.py'), 'r') as fd:
        exec(fd.read(), data)
    return data['__version__']


NAME = 'cloudcrane'
MAIN_PACKAGE = 'cloudcrane'
VERSION = read_version(MAIN_PACKAGE)
DESCRIPTION = 'Deploy application stacks with AWS Cloud Formation and Elastic Container Service (ECS)'
LICENSE = 'Apache License 2.0'
URL = 'https://github.com/ehartung/cloudcrane'
AUTHOR = 'Enrico Hartung'
EMAIL = 'enyo23@gmail.com'

COVERAGE_XML = True
COVERAGE_HTML = False
JUNIT_XML = True
# Add here all kinds of additional classifiers as defined under
# https://pypi.python.org/pypi?%3Aaction=list_classifiers
CLASSIFIERS = [
    'Environment :: Console',
    'Development Status :: 4 - Beta',
    'Programming Language :: Python',
    'Programming Language :: Python :: 3.5',
    'Programming Language :: Python :: Implementation :: CPython',
    'Operating System :: POSIX :: Linux',
    'Operating System :: MacOS :: MacOS X',
    'License :: OSI Approved :: Apache Software License',
    'Topic :: System :: Clustering',
    'Topic :: System :: Installation/Setup'
]

CONSOLE_SCRIPTS = ['cloudcrane = cloudcrane.cli:main']


class PyTest(TestCommand):

    user_options = [
        ('cov=', None, 'Run coverage'),
        ('cov-xml=', None, 'Generate junit xml report'),
        ('cov-html=', None, 'Generate junit html report'),
        ('junitxml=', None, 'Generate xml of test results')
    ]

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.cov = None
        self.cov_xml = False
        self.cov_html = False
        self.junitxml = None

    def finalize_options(self):
        TestCommand.finalize_options(self)
        if self.cov is not None:
            self.cov = ['--cov', self.cov, '--cov-report', 'term-missing']
            if self.cov_xml:
                self.cov.extend(['--cov-report', 'xml'])
            if self.cov_html:
                self.cov.extend(['--cov-report', 'html'])
        if self.junitxml is not None:
            self.junitxml = ['--junitxml', self.junitxml]

    def run_tests(self):
        try:
            import pytest
        except Exception:
            raise RuntimeError('py.test is not installed, run: pip install pytest')
        params = {'args': self.test_args}
        if self.cov:
            params['args'] += self.cov
        if self.junitxml:
            params['args'] += self.junitxml
        params['args'] += ['--doctest-modules', MAIN_PACKAGE, '-s']
        errno = pytest.main(**params)
        sys.exit(errno)


def get_install_requirements(path):
    content = open(os.path.join(__location__, path)).read()
    return [req for req in content.split('\\n') if req != '']


def read(fname):
    return open(os.path.join(__location__, fname), encoding='utf-8').read()


def setup_package():
    # Assemble additional setup commands
    cmdclass = dict()
    cmdclass['test'] = PyTest
    command_options = {'test': {
        'test_suite': ('setup.py', 'tests'), 'cov': ('setup.py', MAIN_PACKAGE)}
    }
    if JUNIT_XML:
        command_options['test']['junitxml'] = 'setup.py', 'junit.xml'
    if COVERAGE_XML:
        command_options['test']['cov_xml'] = 'setup.py', True
    if COVERAGE_HTML:
        command_options['test']['cov_html'] = 'setup.py', True

    setup(
        name=NAME,
        version=VERSION,
        description=DESCRIPTION,
        long_description=read('README.md'),
        author=AUTHOR,
        author_email=EMAIL,
        url=URL,
        license=LICENSE,
        keywords='ecs aws cloud formation cf boto',
        classifiers=CLASSIFIERS,
        test_suite='tests',
        packages=setuptools.find_packages(exclude=['tests', 'tests.*']),
        install_requires=get_install_requirements('requirements.txt'),
        setup_requires=['flake8'],
        cmdclass=cmdclass,
        tests_require=['pytest-cov', 'pytest', 'mock', 'testfixtures'],
        command_options=command_options,
        entry_points={'console_scripts': CONSOLE_SCRIPTS},
    )


if __name__ == '__main__':
    setup_package()

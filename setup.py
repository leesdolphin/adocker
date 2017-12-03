#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The setup script."""

from setuptools import find_packages, setup

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

requirements = [
    'docker',
    'aiodocker',
    'attrs',
]

test_requirements = [
    'pytest',
    'pytest-aiohttp',
    'pytest-asyncio',
    # TODO: put package test requirements here
]

setup(
    name='adocker',
    version='0.1.0',
    description="An AsyncIO implementation of `docker` using `aiodocker`.",
    long_description=readme + '\n\n' + history,
    author="Lee Symes",
    author_email='leesdolphin@gmail.com',
    url='https://github.com/leesdolphin/adocker',
    packages=find_packages(include=['adocker', 'adocker.*']),
    include_package_data=True,
    install_requires=requirements,
    tests_require=test_requirements,
    extras_require={
        'test': test_requirements,
    },
    license="Apache Software License 2.0",
    test_suite='tests',
    zip_safe=False,
    keywords='Docker, AsyncIO',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        'Framework :: AsyncIO',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
)

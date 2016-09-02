#!/usr/bin/env python
# -*- coding: utf-8 -*-


try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('requirements.txt') as req_file:
    requirements = req_file.read().split('\n')

with open('requirements-dev.txt') as req_file:
    requirements_dev = req_file.read().split('\n')

with open('VERSION') as fp:
    version = fp.read().strip()

setup(
    name='save4life-api',
    version=version,
    description="This is the save4life-api project.",
    long_description=readme,
    author="Dirk Uys",
    author_email='dirkcuys@gmail.com',
    url='https://github.com/dirkcuys/save4life-api',
    packages=[
        'save4life-api',
    ],
    package_dir={'save4life-api':
                 'save4life-api'},
    include_package_data=True,
    install_requires=requirements,
    license="BSD",
    zip_safe=False,
    keywords='save4life-api',
    classifiers=[
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Programming Language :: Python :: 2.7',
    ]
)

#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The setup script."""

import io
import os
import re

from setuptools import setup, find_packages


# define function to parse versions
# https://packaging.python.org/en/latest/single_source_version.html
def read(*names, **kwargs):
    with io.open(
        os.path.join(os.path.dirname(__file__), *names),
        encoding=kwargs.get("encoding", "utf8")
    ) as fp:
        return fp.read()


def find_version(*file_paths):
    version_file = read(*file_paths)
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]",
                              version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")


with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

requirements = ['python-dateutil==2.7.5', 'requests']

setup_requirements = ['pytest-runner', ]

test_requirements = ['pytest', ]

setup(
    author="Jun Fan",
    author_email='junf@ebi.ac.uk',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: Scientific/Engineering :: Bio-Informatics',
        'Topic :: Software Development :: Libraries',
    ],
    description=("IMAGE Validation Tool component of the IMAGE Inject Tool"),
    install_requires=requirements,
    license="Apache License",
    long_description=readme + '\n\n' + history,
    include_package_data=True,
    keywords='IMAGE Validation Tool',
    name='image_validation',
    packages=find_packages(include=['image_validation']),
    setup_requires=setup_requirements,
    test_suite='tests',
    tests_require=test_requirements,
    url='https://github.com/cnr-ibba/IMAGE-ValidationTool',
    version=find_version('image_validation', "__init__.py"),
    zip_safe=False,
)

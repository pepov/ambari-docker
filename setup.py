#!/usr/bin/env python

from setuptools import setup, find_packages

from os import path

here = path.abspath(path.dirname(__file__))
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='ambari-docker-utils',
    version='0.1',
    description='Helper scripts to pack ambari to usable Docker images',
    long_description_content_type='text/markdown',
    long_description=long_description,
    author='Eugene Chekanskiy',
    author_email='echekanskiy@gmail.com',
    packages=find_packages(),
    install_requires=['docker', 'jinja2', 'click', 'requests'],
    include_package_data=True,
    zip_safe=False,
    entry_points={
        'console_scripts': [
            'ambari-docker = ambari_docker.cli.ambari_docker:cli'
        ]
    }
)

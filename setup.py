#!/usr/bin/env python

from setuptools import setup, find_packages

setup(
    name='ambari-docker-utils',
    version='0.1',
    description='Helper scripts to pack ambari to usable Docker images',
    author='Eugene Chekanskiy',
    author_email='echekanskiy@gmail.com',
    packages=find_packages(),
    install_requires=['docker', 'jinja2', 'click', 'requests'],
    scripts=['bin/ambari-docker'],
    include_package_data=True,
    zip_safe=False
)

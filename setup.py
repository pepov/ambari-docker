#!/usr/bin/env python

from setuptools import setup
import os


def get_data_files():
    results = {}
    for dirpath, dirnames, filenames in os.walk('templates'):
        for file in filenames:
            file_path = os.path.join(dirpath, file)
            if dirpath not in results:
                results[dirpath] = []
            results[dirpath].append(file_path)
    return results.items()


setup(
    name='ambari-docker-utils',
    version='0.1',
    description='Helper scripts to pack ambari to usable Docker images',
    author='Eugene Chekanskiy',
    author_email='echekanskiy@gmail.com',
    packages=['ambari_docker'],
    zip_safe=False,
    data_files=get_data_files(),
    install_requires=['docker', 'jinja2'],
    scripts=['bin/docker-ambari-image'],
)

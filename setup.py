#!/usr/bin/env python

from setuptools import setup, find_packages
import os
import zipfile


def zip_dir(path, destination):
    zipf = zipfile.ZipFile(destination, 'w', zipfile.ZIP_STORED)
    for root, dirs, files in os.walk(path):
        for file in files:
            zipf.write(os.path.join(root, file))
    zipf.close()


zip_dir(os.path.join(os.path.dirname(__file__), 'templates'), "ambari_docker/data.zip")

setup(
    name='ambari-docker-utils',
    version='0.1',
    description='Helper scripts to pack ambari to usable Docker images',
    author='Eugene Chekanskiy',
    author_email='echekanskiy@gmail.com',
    packages=find_packages(),
    zip_safe=False,
    package_data={"ambari_docker": ["data.zip"]},
    install_requires=['docker', 'jinja2', 'click', 'requests'],
    scripts=['bin/ambari-docker'],
)

#!/usr/bin/env python

from setuptools import setup, find_packages
import os
import tarfile

ROOT_PACKAGE = "ambari_docker"
RES_FILE_ARCHIVE = "data.tar"
SETUP_PY_ROOT = os.path.dirname(__file__)


def dir_to_tar(path, destination):
    prefix = os.path.dirname(path)
    if not prefix.endswith('/'):
        prefix += '/'
    if prefix.startswith('/'):
        prefix = prefix[1:]
    offset = len(prefix)

    def reset(info: tarfile.TarInfo):
        info.uid = info.gid = 0
        info.uname = info.gname = "root"
        if info.name.startswith(prefix):
            info.name = info.name[offset:]
        return info

    tar = tarfile.TarFile(destination, 'w')
    tar.add(path, recursive=True, filter=reset)
    tar.close()


dir_to_tar(os.path.join(SETUP_PY_ROOT, 'templates'), os.path.join(ROOT_PACKAGE, RES_FILE_ARCHIVE))

setup(
    name='ambari-docker-utils',
    version='0.1',
    description='Helper scripts to pack ambari to usable Docker images',
    author='Eugene Chekanskiy',
    author_email='echekanskiy@gmail.com',
    packages=find_packages(),
    zip_safe=False,
    package_data={ROOT_PACKAGE: [RES_FILE_ARCHIVE]},
    install_requires=['docker', 'jinja2', 'click', 'requests'],
    scripts=['bin/ambari-docker'],
)

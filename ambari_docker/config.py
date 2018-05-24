import os
import shutil
import tempfile
import zipfile

import pkg_resources
from jinja2 import Environment, FileSystemLoader

from ambari_docker.utils import Color, StdoutLogger

_config_instance = None


def instance() -> 'Configuration':
    if _config_instance is None:
        raise Exception("No config instance available")
    return _config_instance


class RelEnvironment(Environment):
    """Override join_path() to enable relative template paths."""

    def join_path(self, template, parent):
        return os.path.join(os.path.dirname(parent), template)


class Configuration(object):
    LOG = StdoutLogger()

    def __init__(self):
        self.data_directory = None
        self.jinja_env = None
        self.image_prefix = 'crs'
        self.log_dockerfile = False
        self.log_docker_cmd_output = False
        self.dockerfile_print_color = Color.Red
        self.IMAGE_BUILDER_LOG = StdoutLogger()

    def prepare(self):
        global _config_instance
        self.data_directory = tempfile.mkdtemp()
        stream = pkg_resources.resource_stream("ambari_docker", 'data.zip')
        zip_ref = zipfile.ZipFile(stream, 'r')
        zip_ref.extractall(self.data_directory)
        zip_ref.close()
        stream.close()

        self.jinja_env = RelEnvironment(
            loader=FileSystemLoader(os.path.join(self.data_directory, 'templates'))
        )
        _config_instance = self
        self.LOG.info(f"Extracted data files to {self.data_directory}")

    def cleanup(self):
        try:
            shutil.rmtree(self.data_directory, ignore_errors=True)
        except:
            pass
        self.data_directory = None
        self.jinja_env = None
        global _config_instance
        _config_instance = None
        self.LOG.info(f"Cleared data files directory {self.data_directory}")

    def __enter__(self):
        self.prepare()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()

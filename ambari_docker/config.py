import os
import ambari_docker.utils
from jinja2 import Environment, FileSystemLoader

templates_directory = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "templates"))


class RelEnvironment(Environment):
    """Override join_path() to enable relative template paths."""

    def join_path(self, template, parent):
        return os.path.join(os.path.dirname(parent), template)


jinja_env = RelEnvironment(
    loader=FileSystemLoader(templates_directory)
)

image_prefix = 'crs'

log_dockerfile = False
log_docker_cmd_output = False
dockerfile_print_color = ambari_docker.utils.Color.Red
IMAGE_BUILDER_LOG = ambari_docker.utils.StdoutLogger()

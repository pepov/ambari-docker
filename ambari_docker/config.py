import jinja2
import posixpath as path
from ambari_docker.data import DATA_ROOT


class _RelativeEnvironment(jinja2.Environment):
    def join_path(self, template, parent):
        return path.normpath(path.join(path.dirname(parent), template))


class TemplateTool(object):
    def __init__(self):
        self.env = _RelativeEnvironment(
            loader=jinja2.FileSystemLoader(DATA_ROOT)
        )

    def render(self, template_path, **template_arguments):
        return self.env.get_template(template_path).render(**template_arguments)

    @staticmethod
    def get_template_root(template_path):
        return path.dirname(path.normpath(path.join(DATA_ROOT, template_path)))


TEMPLATE_TOOL = TemplateTool()

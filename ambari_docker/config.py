import posixpath
import tarfile

import jinja2
import pkg_resources

ROOT_PACKAGE = "ambari_docker"
RES_FILE_ARCHIVE = "data.tar"


class DataFilesTemplateLoader(jinja2.BaseLoader):
    def get_source(self, environment, template):
        res_file = tarfile.TarFile(fileobj=pkg_resources.resource_stream(ROOT_PACKAGE, RES_FILE_ARCHIVE))
        res_member = res_file.getmember(template)  # type: tarfile.TarInfo
        if res_member and res_member.isfile():
            return res_file.extractfile(res_member).read().decode(), template, lambda: True
        raise jinja2.TemplateNotFound(template)


class DataFilesEnvironment(jinja2.Environment):
    def join_path(self, template, parent):
        return posixpath.normpath(posixpath.join(posixpath.dirname(parent), template))


class TemplateTool(object):
    def __init__(self):
        self.env = DataFilesEnvironment(
            loader=DataFilesTemplateLoader()
        )

    def render(self, template_path, **template_arguments):
        return self.env.get_template(template_path).render(**template_arguments)

    @staticmethod
    def extract_template_root(template_path, destination):
        template_root = posixpath.dirname(template_path)
        if not template_root.endswith('/'):
            template_root += '/'
        offset = len(template_root)

        res_file = tarfile.TarFile(fileobj=pkg_resources.resource_stream(ROOT_PACKAGE, RES_FILE_ARCHIVE))

        def get_components():
            for info in res_file.getmembers():
                if info.name.startswith(template_root):
                    info.name = info.name[offset:]
                    yield info

        res_file.extractall(destination, members=get_components())


TEMPLATE_TOOL = TemplateTool()

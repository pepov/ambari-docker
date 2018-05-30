import logging
import os
import urllib.parse
from collections import defaultdict
from typing import Union, List

import docker
import docker.errors
import jinja2

from ambari_docker.config import TEMPLATE_TOOL
from ambari_docker.utils import TempDirectory, copy_tree, ProcessRunner, download_file, copy_file

docker_client = docker.from_env()

_os_to_image = {
    'centos7': 'centos:7',
    'amazonlinux2': 'amazonlinux:2'
}

_os_to_template_path = {
    'centos7': 'centos7_amazonlinux2',
    'amazonlinux2': 'centos7_amazonlinux2'
}

_os_to_packages = defaultdict(
    lambda: (),
    {
        'amazonlinux2': ('tar', 'initscripts')
    }
)

# this labels must be equal for new image and base image if exists in base image
_check_equality_labels = ('ambari.repo', 'ambari.build', 'ambari.os')
# this labels in base image must be missing or false in base image
_check_false_labels = ('ambari.server', 'ambari.agent')

LOG = logging.getLogger("DockerImageBuilder")
DOCKERFILE_LOGGER = logging.getLogger("DockerfileLogger")


def _get_base_image_info(base_image_name, repo_os, existing_labels=None):
    if not base_image_name:
        base_image_name = _os_to_image[repo_os]
    try:
        base_image = docker_client.images.get(base_image_name)
    except docker.errors.ImageNotFound:
        LOG.info(f"Pulling base image '{base_image_name}'...")
        base_image = docker_client.images.pull(base_image_name)
        LOG.info(f"Pulled base image '{base_image_name}'")

    if not existing_labels:
        existing_labels = {}

    base_image_labels = {}

    for key, value in base_image.labels.items():
        if key.startswith("ambari."):
            base_image_labels[key] = value
        if key.startswith("hdf."):
            base_image_labels[key] = value
        if key.startswith("hdp."):
            base_image_labels[key] = value

    for label_key in _check_equality_labels:
        if label_key in base_image_labels:
            if label_key in existing_labels:
                if base_image_labels[label_key] != existing_labels[label_key]:
                    raise Exception(f"'{existing_labels}' has value '{base_image_labels[label_key]}',"
                                    f" but wanted {existing_labels[label_key]}")

    for label_key in _check_false_labels:
        if label_key in existing_labels:
            if label_key in base_image_labels and base_image_labels[label_key] == "true":
                raise Exception(f"'{existing_labels}' already presented in image {base_image_name}")

    base_image_labels.update(existing_labels)

    return base_image_name, base_image_labels


class ContextFile(object):
    def __init__(self, source, destination):
        self.source = source
        self.destination = destination
        self.destination_folder = os.path.dirname(self.destination).lstrip("/")

    def copy_to_context(self, context_directory: str):
        context_destination_directory = os.path.join(context_directory, self.destination_folder)
        os.makedirs(context_destination_directory, exist_ok=True)
        context_file_destination = os.path.join(context_directory, self.destination.lstrip("/"))
        if "http" in self.source:
            LOG.info(f"Trying to download '{self.source}' to '{context_file_destination}'")
            download_file(self.source, context_file_destination)
            LOG.info(f"Downloaded '{self.source}' to '{context_file_destination}'")
        else:
            if os.path.exists(self.source):
                copy_file(self.source, context_file_destination)
            else:
                raise Exception(f"Source file '{self.source}' does not exists")


class ContextDirectory(object):
    def __init__(self, source, destination="/"):
        self.source = source
        self.destination = destination.lstrip("/")

    def copy_to_context(self, context_directory: str):
        context_destination_path = os.path.join(context_directory, self.destination)
        LOG.info(f"Copying folder '{self.source}' to '{context_destination_path}'")
        copy_tree(self.source, context_destination_path)


def build_docker_image(
        image_tag: str,
        docker_file_content: str,
        context_data: List[Union[ContextFile, ContextDirectory]] = ()
):
    """
    Builds docker image with tag *image_tag*.

    Files in *base_dir* will be copied to temporary folder.
    *docker_file_content* string will be written to Dockerfile located in temporary folder where files from *base_dir*
    were copied. "docker build" command will be executed in newly created temporary folder.

    We need this kind of hacks in order to make relative path for commands like "COPY" in Dockerfiles work properly.
    """

    with TempDirectory() as tmp_dir:
        LOG.info(
            f"Building docker image '{image_tag}' with context directory '{tmp_dir.path}'...")

        for data in context_data:
            data.copy_to_context(tmp_dir.path)

        if DOCKERFILE_LOGGER.isEnabledFor(logging.DEBUG):
            DOCKERFILE_LOGGER.debug("dockerfile content:")
            for line in docker_file_content.splitlines():
                DOCKERFILE_LOGGER.debug(line.rstrip())

        dockerfile_path = os.path.join(tmp_dir.path, "Dockerfile")
        open(dockerfile_path, "w").write(docker_file_content)

        cmd = f'docker build -t {image_tag} -f Dockerfile .'

        LOG.info(f"Executing '{cmd}' in directory '{tmp_dir.path}'")
        out, code = ProcessRunner(
            cmd,
            cwd=tmp_dir.path
        ).communicate()
        if code != 0:
            LOG.error(f"Failed to build image '{image_tag}'")
            raise Exception(f"Failed to build image '{image_tag}'")
        LOG.info(f"Successfully build image '{image_tag}'")


# def build_stack_image(stack_repo_url: str, base_image_name: str = None, **kwargs) -> str:
#     url = urllib.parse.urlparse(stack_repo_url)
#     path_parts = url.path.split('/')
#
#     repo_os, repo_stack, repo_build = path_parts[-4], path_parts[-5], path_parts[-1]
#     repo_file_url = f"{stack_repo_url.rstrip('/')}/{repo_stack.lower()}bn.repo"
#     repo_name = f"{repo_stack}-{repo_build}"
#     resulting_image_tag = f"{config.image_prefix}/{repo_stack.lower()}:{repo_build}"
#     base_image_name, labels = _get_base_image_info(base_image_name, repo_os)
#
#     labels[f"{repo_stack.lower()}.repo"] = stack_repo_url
#     labels[f"{repo_stack.lower()}.build"] = repo_name
#     labels['ambari.os'] = repo_os
#
#     if labels:
#         kwargs['label'] = " ".join([f'{k}="{v}"' for k, v in labels.items()])
#
#     template = instance().jinja_env.get_template(f"dockerfiles/stack/{repo_os}/Dockerfile")
#     template_directory = os.path.dirname(os.path.abspath(template.filename))
#
#     dockerfile_content = template.render(
#         repo_file_url=repo_file_url,
#         repo_name=repo_name,
#         base_image=base_image_name,
#         **kwargs
#     )
#
#     build_docker_image(resulting_image_tag, template_directory, dockerfile_content, "Dockerfile")
#
#     return resulting_image_tag


def _build_ambari_image(
        ambari_repo_url: str,
        base_image_name: str = None,
        component: str = "server",
        labels=None,
        env=None,
        packages=(),
        context_data=None,
        image_prefix="crs",
        **template_arguments
):
    """
    Builds image with ambari packages installed.
    Dockerfile template will be picked up by *component* argument.

    :param ambari_repo_url: ambari repository url
    :param base_image_name: base image for resulting image
    :param component: component name, can be 'server' or 'agent'
    :param labels: additional labels to be added to resulting image
    :param env_variables: environment variables to be set
    :param packages: packages to be installed in to image, can not be empty
    :param template_arguments: key-value arguments that will be passed to Dockerfile template

    :return: resulting image tag
    """

    if context_data is None:
        context_data = []

    if labels is None:
        labels = {}

    if env is None:
        env = {}
    if not packages:
        raise Exception("Some ambari packages need to be specified")

    url = urllib.parse.urlparse(ambari_repo_url)
    path_parts = url.path.split('/')

    repo_os, repo_stack, repo_build = path_parts[-4], path_parts[-5], path_parts[-1]
    repo_file_url = f"{ambari_repo_url.rstrip('/')}/{repo_stack.lower()}bn.repo"

    # create labels
    labels['ambari.repo'] = ambari_repo_url
    labels['ambari.build'] = repo_build
    labels['ambari.os'] = repo_os
    labels[f'ambari.{component}'] = "true"

    base_image_name, labels = _get_base_image_info(base_image_name, repo_os, labels)

    # some os requires additional packages
    packages = packages + _os_to_packages[repo_os]

    if labels:
        template_arguments['label'] = " ".join([f'{k}="{v}"' for k, v in labels.items()])

    if env:
        template_arguments['environment'] = " ".join([f'{k}="{v}"' for k, v in env.items()])

    template_arguments['packages'] = packages
    template_arguments['base_image'] = base_image_name
    template_arguments['repo_file_url'] = repo_file_url

    template_path = f"templates/dockerfiles/ambari/{_os_to_template_path[repo_os]}/Dockerfile.{component}"
    dockerfile_content = TEMPLATE_TOOL.render(template_path, **template_arguments)
    with TempDirectory() as template_root:
        TEMPLATE_TOOL.extract_template_root(template_path, template_root.path)
        context_data.append(ContextDirectory(template_root.path))
        resulting_image_tag = f"{image_prefix}/ambari/{component}:{repo_build}"

        build_docker_image(
            image_tag=resulting_image_tag,
            docker_file_content=dockerfile_content,
            context_data=context_data
        )

    return resulting_image_tag


def build_ambari_server_image(
        ambari_repo_url: str,
        base_image_name: str = None,
        mpacks=None
):
    if mpacks is None:
        mpacks = []

    template_arguments = {}

    context_data = []
    mpacks_in_container = []

    for mpack in mpacks:
        mpack_name = os.path.basename(mpack)
        mpack_path = f"/mpacks/{mpack_name}"
        context_data.append(ContextFile(mpack, mpack_path))
        mpacks_in_container.append(f"/root/mpacks/{mpack_name}")

    if mpacks_in_container:
        template_arguments["mpacks"] = mpacks_in_container

    packages = ("ambari-server",)

    return _build_ambari_image(
        ambari_repo_url,
        base_image_name,
        "server",
        packages=packages,
        context_data=context_data,
        **template_arguments
    )


def build_ambari_agent_image(
        ambari_repo_url: str,
        base_image_name: str = None
):
    return _build_ambari_image(
        ambari_repo_url,
        base_image_name,
        "agent",
        packages=("ambari-agent",)
    )

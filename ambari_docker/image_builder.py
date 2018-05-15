import os
import sys
import urllib.parse

import docker
import docker.errors

from ambari_docker import config
from ambari_docker.utils import TempDirectory, copytree, ProcessRunner, Color

docker_client = docker.from_env()

_os_to_image = {
    'centos7': 'centos:7'
}

LOG = config.IMAGE_BUILDER_LOG


def _get_base_image_info(base_image_name, repo_os):
    if not base_image_name:
        base_image_name = _os_to_image[repo_os]
    try:
        base_image = docker_client.images.get(base_image_name)
    except docker.errors.ImageNotFound:
        base_image = docker_client.images.pull(base_image_name)

    labels = {}
    for key, value in base_image.labels.items():
        if key.startswith("ambari."):
            labels[key] = value
        if key.startswith("hdf."):
            labels[key] = value
        if key.startswith("hdp."):
            labels[key] = value

    if 'ambari.os' in labels:
        if labels['ambari.os'] != repo_os:
            raise Exception(f"Base image os('{base_image.labels['os']}') is not a repo os '{os}'")

    return base_image_name, labels


def _build_docker_image(image_tag, base_dir, docker_file_content, docker_file_name):
    """
    Builds docker image with tag *image_tag*.

    Files in *base_dir* will be copied to temporary folder.
    *docker_file_content* string will be written to Dockerfile located in temporary folder where files from *base_dir*
    were copied. "docker build" command will be executed in newly created temporary folder.

    We need this kind of hacks in order to make relative path for commands like "COPY" in Dockerfiles work properly.

    :param image_tag:
    :param base_dir:
    :param docker_file_content:
    :param docker_file_name:
    :return:
    """
    with TempDirectory() as tmp_dir:
        LOG.info(f"Building docker image '{image_tag}' with context directory '{tmp_dir.path}'...")
        if config.log_dockerfile:
            LOG.debug("dockerfile content:")
            print(config.dockerfile_print_color.colorize(docker_file_content))
        copytree(base_dir, tmp_dir.path)
        dest_dockerfile = os.path.join(tmp_dir.path, docker_file_name)
        open(dest_dockerfile, "w").write(docker_file_content)

        out, code = ProcessRunner(
            f'docker build -t {image_tag} -f {docker_file_name} .',
            cwd=tmp_dir.path,
            text_color=Color.Cyan,
            prepend_color=Color.Blue,
            silent=not config.log_docker_cmd_output
        ).communicate()
        if code != 0:
            raise Exception(f"Failed to build image {image_tag}")
        LOG.info(f"Successfully build image '{image_tag}'")


def build_stack_image(stack_repo_url: str, base_image_name: str = None, **kwargs) -> str:
    url = urllib.parse.urlparse(stack_repo_url)
    path_parts = url.path.split('/')

    repo_os, repo_stack, repo_build = path_parts[-4], path_parts[-5], path_parts[-1]
    repo_file_url = f"{stack_repo_url.rstrip('/')}/{repo_stack.lower()}bn.repo"
    repo_name = f"{repo_stack}-{repo_build}"
    resulting_image_tag = f"{config.image_prefix}/{repo_stack.lower()}:{repo_build}"
    base_image_name, labels = _get_base_image_info(base_image_name, repo_os)

    labels[f"{repo_stack.lower()}.repo"] = stack_repo_url
    labels[f"{repo_stack.lower()}.build"] = repo_name
    labels['ambari.os'] = repo_os

    if labels:
        kwargs['label'] = " ".join([f'{k}="{v}"' for k, v in labels.items()])

    template = config.jinja_env.get_template(f"dockerfiles/stack/{repo_os}/Dockerfile")
    template_directory = os.path.dirname(os.path.abspath(template.filename))

    dockerfile_content = template.render(
        repo_file_url=repo_file_url,
        repo_name=repo_name,
        base_image=base_image_name,
        **kwargs
    )

    _build_docker_image(resulting_image_tag, template_directory, dockerfile_content, "Dockerfile")

    return resulting_image_tag


def _build_ambari_image(
        ambari_repo_url: str,
        base_image_name: str = None,
        component: str = "server",
        additional_labels=None,
        env_variables=None,
        packages=(),
        **kwargs
):
    """
    Builds image with ambari packages installed.
    Dockerfile template will be picked up by *component* argument.

    :param ambari_repo_url: ambari repository url
    :param base_image_name: base image for resulting image
    :param component: component name, can be 'server' or 'agent'
    :param additional_labels: additional labels to be added to resulting image
    :param env_variables: environment variables to be set
    :param packages: packages to be installed in to image, can not be empty
    :param kwargs: key-value arguments that will be passed to Dockerfile template

    :return: resulting image tag
    """
    if additional_labels is None:
        additional_labels = {}
    if env_variables is None:
        env_variables = {}
    if not packages:
        raise Exception("Some ambari packages need to be specified")

    url = urllib.parse.urlparse(ambari_repo_url)
    path_parts = url.path.split('/')

    repo_os, repo_stack, repo_build = path_parts[-4], path_parts[-5], path_parts[-1]
    repo_file_url = f"{ambari_repo_url.rstrip('/')}/{repo_stack.lower()}bn.repo"
    base_image_name, labels = _get_base_image_info(base_image_name, repo_os)

    if 'ambari.repo' in labels and labels['ambari.repo'] != ambari_repo_url:
        raise Exception(f"Base image already have repo '{ambari_repo_url}'")
    else:
        labels['ambari.repo'] = ambari_repo_url
    if 'ambari.build' in labels and labels['ambari.build'] != repo_build:
        raise Exception(f"Base image already have repo build '{repo_build}'")
    else:
        labels['ambari.build'] = repo_build

    labels['ambari.os'] = repo_os

    if f'ambari.{component}' in labels and labels[f'ambari.{component}'] == "true":
        raise Exception(f"Base image already have ambari-{component}")
    else:
        labels[f'ambari.{component}'] = "true"

    for label_key, label_value in additional_labels.items():
        if label_key in labels and labels[label_key] != label_value:
            raise Exception(f"Base image already have label '{label_key}=\"{labels[label_key]}\"'")
        else:
            labels[label_key] = label_value

    if labels:
        kwargs['label'] = " ".join([f'{k}="{v}"' for k, v in labels.items()])

    if env_variables:
        kwargs['environment'] = " ".join([f'{k}="{v}"' for k, v in env_variables.items()])

    template = config.jinja_env.get_template(f"dockerfiles/ambari/{repo_os}/Dockerfile.{component}")
    template_directory = os.path.dirname(os.path.abspath(template.filename))
    dockerfile_content = template.render(
        repo_file_url=repo_file_url,
        base_image=base_image_name,
        packages=packages,
        **kwargs
    )
    resulting_image_tag = f"{config.image_prefix}/ambari/{component}:{repo_build}"

    _build_docker_image(resulting_image_tag, template_directory, dockerfile_content, f"Dockerfile.{component}")

    return resulting_image_tag


def build_ambari_server_image(ambari_repo_url: str, base_image_name: str = None, install_agent: bool = True):
    add_labels = {"ambari.agent": "true"} if install_agent else {}
    env_variables = {
        "AMBARI_SERVER_INSTALLED": "true",
        "AMBARI_AGENT_INSTALLED": "true"
    } if install_agent else {
        "AMBARI_SERVER_INSTALLED": "true"
    }
    packages = ("ambari-server", "ambari-agent") if install_agent else ("ambari-server",)
    return _build_ambari_image(
        ambari_repo_url,
        base_image_name,
        "server",
        additional_labels=add_labels,
        env_variables=env_variables,
        install_agent=install_agent,
        packages=packages
    )


def build_ambari_agent_image(ambari_repo_url: str, base_image_name: str = None):
    return _build_ambari_image(
        ambari_repo_url,
        base_image_name,
        "agent",
        env_variables={
            "AMBARI_AGENT_INSTALLED": "true"
        },
        packages=("ambari-agent",)
    )

import os
import subprocess
import sys
import urllib.parse
import uuid

import docker
import docker.errors

from ambari_docker.config import jinja_env, image_prefix
from ambari_docker.utils import TempDirectory, copytree

docker_client = docker.from_env()

_os_to_image = {
    'centos7': 'centos:7'
}


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

    if 'ambari.os' in labels:
        if labels['ambari.os'] != repo_os:
            raise Exception(f"Base image os('{base_image.labels['os']}') is not a repo os '{os}'")

    return base_image_name, labels


# def _parse_base_image(base_image_name, repo_os):
#     if not base_image_name:
#         base_image_name = _os_to_image[repo_os]
#     try:
#         base_image = docker_client.images.get(base_image_name)
#     except docker.errors.ImageNotFound:
#         base_image = docker_client.images.pull(base_image_name)
#
#     if 'os' in base_image.labels:
#         if base_image.labels['os'] != repo_os:
#             raise Exception(f"Base image os('{base_image.labels['os']}') is not a repo os '{os}'")
#
#     base_stacks = base_image.labels['stacks'].split(",") if 'stacks' in base_image.labels else []
#     base_builds = base_image.labels['builds'].split(",") if 'builds' in base_image.labels else []
#
#     return base_image_name, base_stacks, base_builds
#
# def build_stack_image(stack_repo_url: str, base_image_name: str = None,
#                       image_name_template="{PREFIX}/{NAME}:{TAG}") -> str:
#     url = urllib.parse.urlparse(stack_repo_url)
#     path_parts = url.path.split('/')
#
#     repo_os, repo_stack, repo_build = path_parts[-4], path_parts[-5], path_parts[-1]
#     repo_file_url = f"{stack_repo_url.rstrip('/')}/{repo_stack.lower()}bn.repo"
#     repo_name = f"{repo_stack}-{repo_build}"
#     resulting_image_tag = image_name_template.format(PREFIX=image_prefix, NAME=repo_stack.lower(),
#                                                      TAG=str(uuid.uuid4()))
#
#     template = jinja_env.get_template(f"dockerfiles/stack/{repo_os}/Dockerfile")
#     template_directory = os.path.dirname(os.path.abspath(template.filename))
#     base_image_name, base_stacks, base_builds = _parse_base_image(base_image_name, repo_os)
#
#     stacks = ",".join(sorted(base_stacks + [repo_stack]))
#     builds = ",".join(sorted(base_builds + [repo_name]))
#
#     labels = [
#         f'repo_os="{repo_os}"',
#         f'stacks="{stacks}"',
#         f'builds="{builds}"'
#     ]
#
#     dockerfile_content = template.render(repo_file_url=repo_file_url, repo_name=repo_name, labels=labels,
#                                          base_image=base_image_name)
#
#     result = subprocess.run(
#         f'docker build -t {resulting_image_tag} -',
#         input=dockerfile_content.encode("UTF-8"),
#         shell=True
#     )
#
#     if result.returncode != 0:
#         raise Exception(f"Failed to build image {resulting_image_tag}")
#     return resulting_image_tag
#
# def append_stack_image(stack_repo_url: str, base_stack_image: str, mix_name: str) -> str:
#     return build_stack_image(stack_repo_url, base_stack_image, "{PREFIX}/" + mix_name + ":{TAG}")

def _build_docker_image(image_tag, base_dir, docker_file_content):
    """
    Builds docker image with tag *image_tag*.

    Files in *base_dir* will be copied to temporary folder.
    *docker_file_content* string will be written to Dockerfile located in temporary folder where files from *base_dir*
    were copied. "docker build" command will be executed in newly created temporary folder.

    We need this kind of hacks in order to make relative path for commands like "COPY" in Dockerfiles work properly.

    :param image_tag:
    :param base_dir:
    :param docker_file_content:
    :return:
    """
    with TempDirectory() as tmp_dir:
        print(f"Dockerfile content:")
        sys.stdout.flush()
        print(docker_file_content, file=sys.stderr)
        print(f"Building image '{image_tag}' in directory '{tmp_dir.path}'...")
        print()

        copytree(base_dir, tmp_dir.path)
        dest_dockerfile = os.path.join(tmp_dir.path, "Dockerfile")
        open(dest_dockerfile, "w").write(docker_file_content)

        subprocess.run(
            f'docker build -t {image_tag} .',
            shell=True,
            cwd=tmp_dir.path
        )


def _build_ambari_image(
        ambari_repo_url: str,
        base_image_name: str = None,
        component: str = "server",
        additional_labels=None,
        **kwargs
):
    """
    Builds image with ambari packages installed.
    Dockerfile template will be picked up by *component* argument.

    :param ambari_repo_url: ambari repository url
    :param base_image_name: base image for resulting image
    :param component: component name, can be 'server' or 'agent'
    :param additional_labels: additional labels to be added to resulting image
    :param kwargs: key-value arguments that will be passed to Dockerfile template

    :return: resulting image tag
    """
    if additional_labels is None:
        additional_labels = {}

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

    template = jinja_env.get_template(f"dockerfiles/ambari/{repo_os}/{component}/Dockerfile")
    template_directory = os.path.dirname(os.path.abspath(template.filename))
    dockerfile_content = template.render(
        repo_file_url=repo_file_url,
        labels=[f'{key}="{value}"' for key, value in labels.items()],
        base_image=base_image_name,
        **kwargs
    )
    resulting_image_tag = f"{image_prefix}/ambari/{component}:{repo_build}"

    _build_docker_image(resulting_image_tag, template_directory, dockerfile_content)

    return resulting_image_tag


def build_ambari_server_image(ambari_repo_url: str, base_image_name: str = None, install_agent: bool = True):
    add_labels = {"ambari.agent": "true"} if install_agent else {}
    return _build_ambari_image(
        ambari_repo_url,
        base_image_name,
        "server",
        additional_labels=add_labels,
        install_agent=install_agent
    )


def build_ambari_agent_image(ambari_repo_url: str, base_image_name: str = None):
    return _build_ambari_image(ambari_repo_url, base_image_name, "agent")

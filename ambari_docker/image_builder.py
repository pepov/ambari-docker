import urllib.parse
import subprocess
import uuid

from ambari_docker.config import jinja_env, image_prefix

import docker
import docker.errors

docker_client = docker.from_env()

_os_to_image = {
    'centos7': 'centos/systemd'
}


def _parse_base_image(base_image_name, repo_os):
    if not base_image_name:
        base_image_name = _os_to_image[repo_os]
    try:
        base_image = docker_client.images.get(base_image_name)
    except docker.errors.ImageNotFound:
        base_image = docker_client.images.pull(base_image_name)

    if 'os' in base_image.labels:
        if base_image.labels['os'] != repo_os:
            raise Exception(f"Base image os('{base_image.labels['os']}') is not a repo os '{os}'")

    base_stacks = base_image.labels['stacks'].split(",") if 'stacks' in base_image.labels else []
    base_builds = base_image.labels['builds'].split(",") if 'builds' in base_image.labels else []

    return base_image_name, base_stacks, base_builds


def build_stack_image(stack_repo_url: str, base_image_name: str = None,
                      image_name_template="{PREFIX}/{NAME}:{TAG}") -> str:
    url = urllib.parse.urlparse(stack_repo_url)
    path_parts = url.path.split('/')

    repo_os, repo_stack, repo_build = path_parts[-4], path_parts[-5], path_parts[-1]
    repo_file_url = f"{stack_repo_url.rstrip('/')}/{repo_stack.lower()}bn.repo"
    repo_name = f"{repo_stack}-{repo_build}"
    resulting_image_tag = image_name_template.format(PREFIX=image_prefix, NAME=repo_stack.lower(),
                                                     TAG=str(uuid.uuid4()))

    template = jinja_env.get_template(f"dockerfiles/stack/{repo_os}/Dockerfile")

    base_image_name, base_stacks, base_builds = _parse_base_image(base_image_name, repo_os)

    stacks = ",".join(sorted(base_stacks + [repo_stack]))
    builds = ",".join(sorted(base_builds + [repo_name]))

    labels = [
        f'repo_os="{repo_os}"',
        f'stacks="{stacks}"',
        f'builds="{builds}"'
    ]

    dockerfile_content = template.render(repo_file_url=repo_file_url, repo_name=repo_name, labels=labels,
                                         base_image=base_image_name)

    result = subprocess.run(
        f'docker build -t {resulting_image_tag} -',
        input=dockerfile_content.encode("UTF-8"),
        shell=True
    )

    if result.returncode != 0:
        raise Exception(f"Failed to build image {resulting_image_tag}")
    return resulting_image_tag


def append_stack_image(stack_repo_url: str, base_stack_image: str, mix_name: str) -> str:
    return build_stack_image(stack_repo_url, base_stack_image, "{PREFIX}/" + mix_name + ":{TAG}")


def build_ambari_server_image(ambari_repo_url: str, base_image_name: str = None):
    ambari_package_image = append_stack_image(ambari_repo_url, base_image_name, "ambari")

    resulting_image_tag = f"ambari/{stack_image.replace(':', '_')}:{build}"
    # TODO implement this


# build_ambari_server_image("http://s3.amazonaws.com/dev.hortonworks.com/ambari/centos7/2.x/BUILDS/2.7.0.0-451",
#                           "crs/hdf/centos7:3.2.0.0-275")
# print(build_stack_image("http://s3.amazonaws.com/dev.hortonworks.com/HDF/centos7/3.x/BUILDS/3.2.0.0-275"))
print(append_stack_image("http://s3.amazonaws.com/dev.hortonworks.com/HDP/centos7/3.x/BUILDS/3.0.0.0-1296",
                         "crs/hdf:420f8209-ef9c-462d-8d86-4bd49dec3788", "hdp_hdf"))

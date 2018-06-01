#!/usr/bin/env python3
import logging
import typing

import click

from ambari_docker.config import TEMPLATE_TOOL
from ambari_docker.image_builder import build_ambari_agent_image, build_ambari_server_image

LOG = logging.getLogger("AmbariDocker")

LOGGING_CONFIG = {
    "version": 1,
    "formatters": {
        "subcommand": {
            "format": '\033[0;34m===> %(message)s\033[0m'
        },
        "dockerfile": {
            "format": '\033[0;32m%(message)s\033[0m'
        },
        "default": {
            "format": '%(asctime)-15s [%(levelname)s] [%(name)s] %(message)s'
        }
    },

    "handlers": {
        "subcommand": {
            "()": "ambari_docker.utils.StdOutHandler",
            "formatter": "subcommand",
            "level": "DEBUG"
        },
        "dockerfile": {
            "()": "ambari_docker.utils.StdOutHandler",
            "formatter": "dockerfile",
            "level": "DEBUG"
        },
        "default": {
            "()": "ambari_docker.utils.StdOutHandler",
            "formatter": "default",
            "level": "DEBUG"
        }
    },

    "loggers": {
        "AmbariDocker": {
            "handlers": ["default"]
        },
        "DockerImageBuilder": {
            "handlers": ["default"]
        },
        "ProcessRunner": {
            "handlers": ["subcommand"],
            "level": "DEBUG"
        },
        "DockerfileLogger": {
            "handlers": ["dockerfile"],
            "level": "DEBUG"
        },
        '': {
            'level': 'DEBUG'
        }
    }

}

IMAGE_SHORT_HELP = "build ambari images"
COMPOSE_SHORT_HELP = "create compose file"

IMAGE_REPOSITORY = {
    "required": True,
    "help": "repository to use for image building"
}

IMAGE_INCLUDE_AGENT = {
    "default": True,
    "show_default": True,
    "help": "include or exclude agent in ambari-server image"
}

IMAGE_SERVER_BASE_IMAGE = {
    "default": None,
    "help": "server base image, if not specified, will be extracted from repository"
}

IMAGE_AGENT_BASE_IMAGE = {
    "default": None,
    "help": "agent base image, if not specified, will be extracted from repository"
}
IMAGE_MPACKS = {
    "default": [],
    "multiple": True,
    "help": "specify mpack to install, can be used multiple times, prepend path with 'purge+' to install mpack with"
            " purge option"
}

COMPOSE_SUFFIX = {
    "help": "suffix to distinct container names",
    "show_default": True,
    "default": "cl1"
}
COMPOSE_NODE_COUNT = {
    "help": "count of agent nodes",
    "show_default": True,
    "default": 1,
    "type": click.INT
}

COMPOSE_MEMORY = {
    "help": "node memory limit",
    "show_default": True,
    "default": "2G",
    "type": click.STRING
}

COMPOSE_NODE_TEMPLATE = {
    "help": "node name template, currently accept 'number' argument(node number)",
    "show_default": True,
    "default": "node.{number}",
    "type": click.STRING
}

COMPOSE_SERVER_NAME = {
    "help": "server node name",
    "show_default": True,
    "default": "server",
    "type": click.STRING
}

COMPOSE_NETWORK_NAME = {
    "help": "network name to use in cluster",
    "show_default": True,
    "default": "ambari.test",
    "type": click.STRING
}

COMPOSE_SERVER_IMAGE = {
    "help": "server image to use",
    "show_default": True,
    "default": None,
    "type": click.STRING
}

COMPOSE_AGENT_IMAGE = {
    "help": "agent image to use",
    "show_default": True,
    "default": None,
    "type": click.STRING
}

COMPOSE_OUTPUT = {
    "help": "file path to output resulting compose file",
    "show_default": True,
    "default": "ambari.yml",
    "type": click.Path()
}

COMPOSE_LXCFS = {
    "help": "include lxcfs volumes",
    "show_default": True,
    "is_flag": True,
    "default": False
}


class PipelineCommand(object):
    def __init__(self, order, name, callback, **kwargs):
        self.name = name
        self.order = order
        self.callback = callback
        self.args = kwargs


@click.group(chain=True)
@click.option('--log-level', type=click.Choice(['INFO', 'DEBUG']), default="INFO", show_default=True)
def cli(log_level):
    """
    Command line tool to deal with ambari and docker.

    Commands can be pipelined and previous command result will be passed to next command.

    For example in command "ambari-docker image -r http://test.repo compose -o example.compose" images produced by
    "image" command will be used in "compose" command(this means that '--server-image' and '--agent-image' options
    for "compose" command can be omitted).
    """
    for name, handler in LOGGING_CONFIG["handlers"].items():
        handler["level"] = log_level
    for name, logger in LOGGING_CONFIG["loggers"].items():
        logger["level"] = log_level

    import logging.config
    logging.config.dictConfig(LOGGING_CONFIG)


@cli.resultcallback()
def process_pipeline(processors, log_level):
    previous_command_context = {}
    for pipeline_command in sorted(processors, key=lambda x: x.order):
        previous_command_context = pipeline_command.callback(context=previous_command_context, **pipeline_command.args)
        if not previous_command_context:
            previous_command_context = {}


@cli.command(short_help=IMAGE_SHORT_HELP)
@click.option('-r', '--repository', **IMAGE_REPOSITORY)
@click.option('+agent/-agent', 'include_agent', **IMAGE_INCLUDE_AGENT)
@click.option('-sbi', '--server-base-image', **IMAGE_SERVER_BASE_IMAGE)
@click.option('-abi', '--agent-base-image', **IMAGE_AGENT_BASE_IMAGE)
@click.option('-m', '--mpack', **IMAGE_MPACKS)
def image(**kwargs):
    """
    Command to build ambari server and agent docker images.
    """

    def callback(
            context: object,
            repository: str,
            include_agent: bool,
            server_base_image: str,
            agent_base_image: str,
            mpack: typing.List[str]
    ):
        agent_image = build_ambari_agent_image(repository, agent_base_image)
        server_base_image = agent_image if include_agent else server_base_image
        server_image = build_ambari_server_image(repository, server_base_image, mpacks=mpack)

        LOG.info(f"Resulting agent image :{agent_image}")
        LOG.info(f"Resulting server image:{server_image}")

        return {"server_image": server_image, "agent_image": agent_image}

    return PipelineCommand(0, "image", callback, **kwargs)


@cli.command(short_help=COMPOSE_SHORT_HELP)
@click.option('-o', '--output', **COMPOSE_OUTPUT)
@click.option('-s', '--suffix', **COMPOSE_SUFFIX)
@click.option('-n', '--node-count', **COMPOSE_NODE_COUNT)
@click.option('-m', '--memory', **COMPOSE_MEMORY)
@click.option('-nt', '--node-template', **COMPOSE_NODE_TEMPLATE)
@click.option('-sn', '--server-name', **COMPOSE_SERVER_NAME)
@click.option('-nn', '--network-name', **COMPOSE_NETWORK_NAME)
@click.option("-si", "--server-image", **COMPOSE_SERVER_IMAGE)
@click.option("-ai", "--agent-image", **COMPOSE_AGENT_IMAGE)
@click.option("--lxcfs", **COMPOSE_LXCFS)
def compose(**kwargs):
    """
    Command to generate docker-compose file based on requested parameters.
    Note, "--server-image" and "--agent-image" "image" command specified in pipeline.
    In this case images produced by "image" command will be used.
    """

    def callback(
            context: object,
            output: str,
            suffix: str,
            node_count: int,
            memory: str,
            node_template: str,
            server_name: str,
            network_name: str,
            server_image: str,
            agent_image: str,
            lxcfs
    ):
        if isinstance(context, dict):
            if agent_image is None:
                if "agent_image" in context:
                    agent_image = context["agent_image"]
            if server_image is None:
                if "server_image" in context:
                    server_image = context["server_image"]
        if agent_image is None or server_image is None:
            click.get_current_context().fail("'--server-image' and '--agent-image' must be specified")

        nodes = []
        for i in range(int(node_count)):
            nodes.append(node_template.format(number=i))

        result = TEMPLATE_TOOL.render(
            "templates/docker-compose.yml",
            server_hostname=server_name,
            domain=network_name,
            nodes=nodes,
            server_image=server_image,
            agent_image=agent_image,
            suffix=suffix,
            memory=memory,
            lxcfs=lxcfs)

        LOG.info(f"Writing compose file to '{output}'")
        open(output, "w").write(result)

    return PipelineCommand(2, "compose", callback, **kwargs)


if __name__ == "__main__":
    cli()

# Welcome to ambari_docker

ambari_docker is a set of python modules and command-line scripts to build docker images with Ambari Server and Ambari Agent. As result you will have ready-to-use images with preconfigured Ambari to run in docker.

# Image description
Both, ambari-agent and ambari-server images have common base - supervisord instance as ENTRYPOINT for container and scripts that wraps ambari-server and ambari-agent daemons to make look them as foreground processes.
#### Ambari Server Image
Nothing outstanding here. Regular ambari server setup with embedded postgresql server. One note: this image contains ugly hack that mocks systemctl util in order to make `systemctl start postgresql.service` command working fine without systemd. This is required because `ambari-server setup -s` command trying to invoke systemctl to manage postgresql server.

*TODO:*
- [] make image configurable with external database instance
#### Ambari Agent Image
This image contains a little bit of magic. Wrapper script, started by supervisord will accept environment variable *AMBARI_SERVER_HOSTNAME* which must contain fqdn of ambari-server host/container/whatever. This fqnd will be used as server address for ambari agent.

Also this image requires to have extra capabilities: CAP_RESOURCE and maybe CAP_ADMIN(use it too for 100% working hadoop services) in order to run some specific hadoop services. This capabilities required because of some services and scripts in ambari trying to mess with ulimits and other system settings.

For sure, granting additional capabilities is not secure, but this scripts MUST NOT be used in production, only for testing purposes.

*TODO:*
- [] tight required capabilities as much as possible
# Binaries
#### docker-ambari-image
```
eugene@eugene-work:~$ docker-ambari-image --help
usage: docker-ambari-image [-h] [-s] [-c] [-sic] -r REPOSITORY
                           [-sbi SERVER_BASE_IMAGE] [-abi AGENT_BASE_IMAGE]
                           [-v] [-vv] [-m MPACKS [MPACKS ...]]

Simple script to build docker images with Ambari Server and Ambari Agent
daemons in it. Images will contain necessary bits to run server and agent on
container startup. DO NOT provide CMD or ENTRYPOINT for resulting images, they
already configured to start supervisorctl.

optional arguments:
  -h, --help            show this help message and exit
  -s, --server          build server image
  -c, --client          build client image
  -sic, --server-include-client
                        server image will include client as well
  -r REPOSITORY, --repository REPOSITORY
                        ambari repository url
  -sbi SERVER_BASE_IMAGE, --server-base-image SERVER_BASE_IMAGE
                        server base image
  -abi AGENT_BASE_IMAGE, --agent-base-image AGENT_BASE_IMAGE
                        agent base image
  -v, --verbose         print docker commands output
  -vv, --very-verbose   print docker commands output and docker files content
  -m MPACKS [MPACKS ...], --mpacks MPACKS [MPACKS ...]
                        mpack to be included in server image

```
#### docker-ambari-compose
```
eugene@eugene-work:~$ docker-ambari-compose --help
usage: docker-ambari-compose [-h] [-nc NODE_COUNT] [-m MEMORY]
                             [-an AGENT_NAME] [-sn SERVER_NAME]
                             [-nn NETWORK_NAME] [-si SERVER_IMAGE]
                             [-ai AGENT_IMAGE] [-l]

Tool for generation of docker-compose.yml file based on ambari images.

optional arguments:
  -h, --help            show this help message and exit
  -nc NODE_COUNT, --node-count NODE_COUNT
                        count of agent nodes(default=1)
  -m MEMORY, --memory MEMORY
                        memory limit per container(default=2G)
  -an AGENT_NAME, --agent-name AGENT_NAME
                        agent node name template(default=node.{number})
  -sn SERVER_NAME, --server-name SERVER_NAME
                        server node name template(default=server)
  -nn NETWORK_NAME, --network-name NETWORK_NAME
                        network name(default=ambari.test)
  -si SERVER_IMAGE, --server-image SERVER_IMAGE
                        server image
  -ai AGENT_IMAGE, --agent-image AGENT_IMAGE
                        agent image
  -l, --list            list available images

```
# Usage

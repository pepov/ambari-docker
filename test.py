# from jinja2 import Environment, FileSystemLoader
# env = Environment(
#     loader=FileSystemLoader('./templates')
# )

# template = env.get_template('docker-compose.yml')
# print(template.render(nodes=["node1", "node2", "node3"], server_image="ambari:123", agent_image="agent:123", suffix="cl1", domain="test.org"))

import docker

docker_client = docker.from_env()
image = docker_client.images.get("crs/hdf:420f8209-ef9c-462d-8d86-4bd49dec3788")
pass
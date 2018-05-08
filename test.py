
# from ambari_docker.image_builder import build_ambari_server_image, build_ambari_agent_image
#
# print(build_ambari_agent_image("http://s3.amazonaws.com/dev.hortonworks.com/ambari/centos7/2.x/BUILDS/2.7.0.0-465"))
from ambari_docker import config
compose_template = config.jinja_env.get_template("docker-compose.yml")

result = compose_template.render(
    server_hostname="server",
    domain="test.org",
    nodes=["node1", "node2"],
    server_image="crs/ambari/server:2.7.0.0-465",
    agent_image="crs/ambari/agent:2.7.0.0-465",
    suffix="cl1"
)

print(result)

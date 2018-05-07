
from ambari_docker.image_builder import build_ambari_server_image

print(build_ambari_server_image("http://s3.amazonaws.com/dev.hortonworks.com/ambari/centos7/2.x/BUILDS/2.7.0.0-465", install_agent=True))
# from ambari_docker import config
# compose_template = config.jinja_env.get_template("docker-compose.yml")
#
# result = compose_template.render(
#     server_hostname="server",
#     domain="test.org",
#     nodes=["node1", "node2"],
#     server_image="server_image:123",
#     agent_image="agent_image:123",
#     suffix="echekanskiy"
# )
#
# print(result)

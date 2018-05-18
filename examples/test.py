from ambari_docker import config
compose_template = config.jinja_env.get_template("docker-compose.yml")

result = compose_template.render(
    server_hostname="server",
    domain="test.org",
    nodes=["node1", "node2"],
    server_image="crs/ambari/server:2.7.0.0-510",
    agent_image="crs/ambari/agent:2.7.0.0-510",
    suffix="cl1"
)

print(result)

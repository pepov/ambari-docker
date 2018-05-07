from ambari_docker import config

compose_template = config.jinja_env.get_template("docker-compose.yml")

result = compose_template.render(
    server_hostname="server",
    domain="test.org",
    nodes=["node1", "node2"],
    server_image="server_image:123",
    agent_image="agent_image:123",
    suffix="echekanskiy"
)

print(result)

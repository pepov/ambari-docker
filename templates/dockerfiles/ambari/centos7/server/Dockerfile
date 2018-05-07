FROM {{ base_image }}
MAINTAINER "Eugene Chekanskiy" <echekanskiy@hortonworks.com>
{%- for label in labels %}
LABEL {{ label }}
{%- endfor %}
COPY systemctl /usr/bin
RUN chmod 755 /usr/bin/systemctl && chown root:root /usr/bin/systemctl
RUN curl {{ repo_file_url }} > /etc/yum.repos.d/ambari.repo
RUN yum install ambari-server -y
{%- if install_agent %}
RUN yum install ambari-agent -y
{%- endif %}
RUN ambari-server setup -s || systemctl stop postgresql; sleep 5 && ambari-server setup -s

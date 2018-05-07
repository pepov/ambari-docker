FROM {{ base_image }}
MAINTAINER "Eugene Chekanskiy" <echekanskiy@hortonworks.com>
{%- if label is defined %}
LABEL {{ label }}
{%- endif %}
{%- if environment is defined %}
ENV {{ environment }}
{%- endif %}
COPY systemctl start-ambari-server /usr/bin/
RUN chmod 755 /usr/bin/systemctl && chown root:root /usr/bin/systemctl && \
    chmod 755 /usr/bin/start-ambari-server && chown root:root /usr/bin/start-ambari-server
RUN curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py && python get-pip.py && rm -f get-pip.py && \
    yum group install "Development Tools" -y && yum install python-devel -y && pip install psutil requests
RUN curl {{ repo_file_url }} > /etc/yum.repos.d/ambari.repo && \
    yum install ambari-server {% if install_agent %}ambari-agent {% endif -%} -y
RUN ambari-server setup -s || systemctl stop postgresql; sleep 5 && ambari-server setup -s
# TODO use supervisord as init process
# TODO start ssh daemon
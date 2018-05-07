FROM {{ base_image }}
MAINTAINER "Eugene Chekanskiy" <echekanskiy@hortonworks.com>
{%- for label in labels %}
LABEL {{ label }}
ENV {{ label }}
{%- endfor %}
RUN curl {{ repo_file_url }} > /etc/yum.repos.d/ambari.repo
RUN yum install ambari-agent -y

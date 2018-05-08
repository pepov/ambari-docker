FROM {{ base_image }}
MAINTAINER "Eugene Chekanskiy" <echekanskiy@hortonworks.com>
{%- if label is defined %}
LABEL {{ label }}
{%- endif %}
RUN curl {{ repo_file_url }} > /etc/yum.repos.d/{{ repo_name }}.repo
RUN repoquery --disablerepo=* --enablerepo={{ repo_name }} -a | xargs yum -y --skip-broken install
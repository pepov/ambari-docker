FROM {{ base_image }}
MAINTAINER "Eugene Chekanskiy" <echekanskiy@hortonworks.com>
{%- for label in labels %}
LABEL {{ label }}
{%- endfor %}
RUN yum install wget -y
RUN wget {{ repo_file_url }} -O /etc/yum.repos.d/tmp.repo
RUN repoquery --disablerepo=* --enablerepo={{ repo_name }} -a | xargs yum -y --skip-broken install && rm -rf /etc/yum.repos.d/tmp.repo
CMD ["/usr/sbin/init"]
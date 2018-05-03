ARG IMAGE
FROM $IMAGE
MAINTAINER "Eugene Chekanskiy" <echekanskiy@hortonworks.com>
ARG AMBARI_REPO
RUN yum install wget -y
RUN wget $AMBARI_REPO -O /etc/yum.repos.d/ambari.repo
RUN yum install ambari-agent -y
CMD ["/usr/sbin/init"]

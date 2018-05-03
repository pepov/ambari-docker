FROM centos/systemd
MAINTAINER "Eugene Chekanskiy" <echekanskiy@hortonworks.com>
RUN yum install wget -y
RUN wget http://s3.amazonaws.com/dev.hortonworks.com/HDF/centos7/3.x/BUILDS/3.2.0.0-270/hdfbn.repo -O /etc/yum.repos.d/ambari.repo
RUN repoquery --disablerepo=* --enablerepo=HDF-3.2.0.0-270 -a | xargs yum -y install
CMD ["/usr/sbin/init"]

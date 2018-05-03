#!/usr/bin/env bash
# temp variables
INTERMEDIATE_NAME=$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 32 | head -n 1)
INTERMEDIATE_IMAGE=$(cat /dev/urandom | tr -dc 'a-z' | fold -w 32 | head -n 1)
# configuration options
AMBARI_REPO=http://s3.amazonaws.com/dev.hortonworks.com/ambari/centos7/2.x/BUILDS/2.7.0.0-439/ambaribn.repo
IMAGE=ambari/hdf:3.2.0.0-270
RESULT_TAG=2.7.0.0-439

docker build --build-arg IMAGE=$IMAGE --build-arg AMBARI_REPO=$AMBARI_REPO -t $INTERMEDIATE_IMAGE .
docker run --privileged --name $INTERMEDIATE_NAME -v /sys/fs/cgroup:/sys/fs/cgroup:ro -p 8080:8080 -h ambari.agent -d $INTERMEDIATE_IMAGE && \
docker exec -it $INTERMEDIATE_NAME bash -c "sed -i 's/localhost/server.cl1.test.org/g' /etc/ambari-agent/conf/ambari-agent.ini && systemctl enable ambari-agent" && \
docker stop $INTERMEDIATE_NAME && \
docker commit $INTERMEDIATE_NAME ambari/agent:$RESULT_TAG
docker rm $INTERMEDIATE_NAME
docker rmi $INTERMEDIATE_IMAGE

FROM ubuntu:23.04

ARG HOST_PWD

# Install required packages
RUN DEBIAN_FRONTEND=noninteractive \
  apt-get update \
  && apt-get install -y python3 python3-jinja2 openssl openjdk-17-jdk git-crypt curl

# Install docker-compose
RUN curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
RUN chmod +x /usr/local/bin/docker-compose

# Mount docker socket 
VOLUME /var/run/docker.sock
WORKDIR ${HOST_PWD}

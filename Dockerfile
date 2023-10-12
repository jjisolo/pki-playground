FROM ubuntu:23.04

RUN DEBIAN_FRONTEND=noninteractive \
  apt-get update \
  && apt-get install -y python3 python3-jinja2 openssl openjdk-17-jdk

WORKDIR /pki_playground

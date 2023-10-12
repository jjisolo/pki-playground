#!/bin/bash

DOCKER_IMAGE="sirin_pki_playground"
if ! docker image inspect "$DOCKER_IMAGE" &> /dev/null; then
  echo "Docker image '$DOCKER_IMAGE' does not exist. Please build it first with 'docker build . -t $DOCKER_IMAGE'"
  exit 1
fi

docker run -it -v "$(pwd)":/pki_playground "$DOCKER_IMAGE" /bin/sh


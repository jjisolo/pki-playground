#!/bin/bash

DOCKER_IMAGE="sirin_pki_playground"
if ! docker image inspect "$DOCKER_IMAGE" &> /dev/null; then
	echo "Building docker container image..."
	docker build . -t $DOCKER_IMAGE --build-arg HOST_PWD=$PWD 
fi

docker run -it -v "$(pwd)":"$(pwd)" -v /etc/hosts:/etc/hosts -v /var/run/docker.sock:/var/run/docker.sock "$DOCKER_IMAGE" /bin/sh


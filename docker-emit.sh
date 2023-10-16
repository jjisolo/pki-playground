#!/bin/bash

DOCKER_IMAGE="sirin_pki_playground"
if ! docker image inspect "$DOCKER_IMAGE" &> /dev/null; then
	echo "Building docker container image..."
	docker build . -t $DOCKER_IMAGE
fi

docker run -it -v "$(pwd)":/pki_playground "$DOCKER_IMAGE" /bin/sh


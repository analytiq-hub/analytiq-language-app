#!/bin/bash

DOCKER_CONTAINER_NAME=analytiq

cd "$(dirname "$0")"/..
docker build -t $DOCKER_CONTAINER_NAME --progress=plain .

FROM ubuntu:20.04

ENV DEBIAN_FRONTEND=noninteractive

# A minimum number of packages required to install CUDA
RUN apt-get update; apt-get install -y \
    apt-utils \
    curl \
    gnupg \
    wget \
    zip

RUN pip3 install --default-timeout=300 --verbose --no-cache-dir torch

# Install the other requirements
COPY ../requirements.txt /tmp
RUN pip3 install --default-timeout=300 -r /tmp/requirements.txt && \
    rm -f /tmp/requirements.txt
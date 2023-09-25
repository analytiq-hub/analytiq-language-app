FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

# A minimum number of packages required to install CUDA
RUN apt-get update && apt-get install -y \
    apt-utils \
    curl \
    gnupg \
    wget \
    zip

RUN apt-get install software-properties-common \
    && add-apt-repository ppa:deadsnakes/ppa \
    && apt install python3.10 \
    && curl https://bootstrap.pypa.io/get-pip.py -o /tmp/get-pip.py \
    && python3 /tmp/get-pip.py \
    && rm -f /tmp/get-pip.py

RUN pip3 install --default-timeout=300 --verbose --no-cache-dir torch

# Install the other requirements
COPY requirements.txt /tmp
RUN pip3 install --default-timeout=300 -r /tmp/requirements.txt && \
    rm -f /tmp/requirements.txt
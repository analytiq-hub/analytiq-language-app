FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

# A minimum number of packages to get the system running
RUN apt-get update && apt-get install -y \
    apt-utils \
    curl \
    gnupg \
    wget \
    zip \
    sudo

#RUN apt-get install software-properties-common \
#    && add-apt-repository ppa:deadsnakes/ppa


#RUN apt-get install -y python3.10 \
#    && curl https://bootstrap.pypa.io/get-pip.py -o /tmp/get-pip.py \
#    && python3 /tmp/get-pip.py \
#    && rm -f /tmp/get-pip.py

#RUN pip3 install --default-timeout=300 --verbose --no-cache-dir torch

# Install the other requirements
#COPY requirements.txt /tmp
#RUN pip3 install --default-timeout=300 -r /tmp/requirements.txt && \
#    rm -f /tmp/requirements.txt
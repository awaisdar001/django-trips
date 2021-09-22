# syntax=docker/dockerfile:1

# For more information, please refer to https://aka.ms/vscode-docker-python
FROM python:3.8-slim-buster

EXPOSE 8888

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE 1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED 1


WORKDIR /app/dt
ADD . /app/dt

WORKDIR /app/dt

RUN apt-get update && apt-get install -y python3-setuptools \
    python3-pip \
    default-libmysqlclient-dev \
    git \
    nano \
    && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*


RUN pip3 install --upgrade pip

# Install pip requirements
ADD requirements.txt .
RUN python -m pip install -r requirements.txt

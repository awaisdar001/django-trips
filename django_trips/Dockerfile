# For more information, please refer to https://aka.ms/vscode-docker-python
FROM python:3.7-slim

EXPOSE 8888

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE 1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED 1


WORKDIR /app/djangotrips
ADD . /app/djangotrips

WORKDIR /app/djangotrips

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



# During debugging, this entry point will be overridden. For more information, please refer to https://aka.ms/vscode-docker-python-debug
# File wsgi.py was not found in subfolder:Django-React-Redux-Frontend. Please enter the Python path to wsgi file.
# CMD ["gunicorn", "--bind", "0.0.0.0:9990", "pythonPath.to.wsgi"]

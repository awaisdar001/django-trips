# For more information, please refer to https://aka.ms/vscode-docker-python
FROM python:3.7-slim

EXPOSE 9990

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE 1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED 1


WORKDIR /trips/app/djreact
ADD . /trips/app/djreact

RUN apt-get update
RUN apt-get -y install python3-pip
RUN apt-get -y install default-libmysqlclient-dev
RUN apt-get -y install git

# Install pip requirements
ADD requirements.txt .
RUN python -m pip install -r requirements.txt


# Install Node.js
RUN apt-get install curl -y
# get install script and pass it to execute:
RUN curl -sL https://deb.nodesource.com/setup_12.x | bash
# and install node
RUN apt-get install nodejs -y
# confirm that it was successful
RUN node -v
# npm installs automatically
RUN npm -v
# Install npm packages
RUN npm install


# Switching to a non-root user, please refer to https://aka.ms/vscode-docker-python-user-rights
RUN useradd appuser && chown -R appuser /trips
USER appuser

# During debugging, this entry point will be overridden. For more information, please refer to https://aka.ms/vscode-docker-python-debug
# File wsgi.py was not found in subfolder:Django-React-Redux-Frontend. Please enter the Python path to wsgi file.
# CMD ["gunicorn", "--bind", "0.0.0.0:9990", "pythonPath.to.wsgi"]

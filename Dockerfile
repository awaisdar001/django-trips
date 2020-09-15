# For more information, please refer to https://aka.ms/vscode-docker-python
FROM python:3.7-slim

EXPOSE 9990

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE 1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED 1


WORKDIR /app/django-trips
ADD . /app/django-trips

RUN apt-get update && \
    apt-get install -y git default-libmysqlclient-dev python3-pip

RUN pip install --upgrade pip
# Install pip requirements
ADD requirements.txt .
RUN python -m pip install -r requirements.txt


# Switching to a non-root user, please refer to https://aka.ms/vscode-docker-python-user-rights
#RUN useradd appuser && chown -R appuser /trips
#USER appuser

# During debugging, this entry point will be overridden. For more information, please refer to https://aka.ms/vscode-docker-python-debug
# File wsgi.py was not found in subfolder:Django-React-Redux-Frontend. Please enter the Python path to wsgi file.
# CMD ["gunicorn", "--bind", "0.0.0.0:9990", "pythonPath.to.wsgi"]

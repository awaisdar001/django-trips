# syntax=docker/dockerfile:1
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

ADD . /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libmariadb-dev \
    pkg-config \
    python3-dev \
    libssl-dev \
    libffi-dev\
    gcc \
    g++ \
    build-essential \
    default-libmysqlclient-dev \
    pkg-config \
    libssl-dev \
    nano \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Copy project
COPY . .

EXPOSE 8000
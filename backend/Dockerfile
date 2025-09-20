# pull official base image
FROM python:3.11-slim-bullseye

# set work directory
WORKDIR /srv/app

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# install dependencies
RUN pip install --upgrade pip
COPY ./requirements.txt .

RUN apt-get update && apt-get install -y \
  gcc \
  netcat \
  libpq-dev \
  postgresql-client \
  dos2unix \
  && apt-get clean

# install temp dependencies for build of pyscopg2 etc
RUN pip install -r requirements.txt

# copy entrypoint.sh
COPY ./entrypoint.sh .

# copy project
COPY . .

# make sure entrypoint.sh can be run in the container
RUN dos2unix ./entrypoint.sh

# run entrypoint.sh
ENTRYPOINT ["/srv/app/entrypoint.sh"]
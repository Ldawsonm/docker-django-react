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
  && apt-get clean

# install temp dependencies for build of pyscopg2 etc
RUN pip install -r requirements.txt

# copy entrypoint.sh
COPY ./entrypoint.sh .

# copy project
COPY . .

# make sure entrypoint.sh can be run in the container
RUN apt-get update && apt-get install -y dos2unix \
    && dos2unix /app/entrypoint.sh \
    && chmod +x /app/entrypoint.sh

# run entrypoint.sh
ENTRYPOINT ["/srv/app/entrypoint.sh"]
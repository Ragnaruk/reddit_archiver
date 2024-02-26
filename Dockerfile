FROM python:3.11

ENV PYTHONPATH /reddit_archiver

WORKDIR /reddit_archiver
COPY ./requirements.txt /reddit_archiver/requirements.txt

RUN pip install -r /reddit_archiver/requirements.txt

COPY . /reddit_archiver
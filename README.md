# Reddit Archiver
[![License](https://img.shields.io/badge/license-MIT-lightgrey.svg)](https://github.com/Ragnaruk/external_grader/blob/master/LICENSE)
[![Code Style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

## Table of Contents
* [Description](#Description)
* [Configuration](#Configuration)
    * [Structure](#Structure)
* [Running](#Running)
    * [Docker](#Docker)
    * [No Docker](#No-Docker)
* [Logging](#Logging)
* [Data Storage](#Data-Storage)

## Description
A telegram bot created to sidestep 1000 saved posts limit on Reddit.

It saves user's posts to internal database every night and allows their viewing through Telegram.

## Configuration
Default path: `/data/config.py`.

### Structure
```python
from pathlib import Path

PATH_DIRECTORY = Path().cwd() / "data"
PATH_DIRECTORY.mkdir(parents=True, exist_ok=True)

PATH_LOGS = PATH_DIRECTORY / "logs"
PATH_LOGS.mkdir(parents=True, exist_ok=True)

PATH_DB = PATH_DIRECTORY / "db.json"
PATH_PERSISTENCE = PATH_DIRECTORY / "persistence.pickle"

# Reddit

# Bot name - "<platform>:<name>:v<version> (by /u/<username>)"
USER_AGENT = ""
# Reddit client id/secret
HTTP_AUTH_LOGIN = ""
HTTP_AUTH_PASSWORD = ""
# Reddit login/password
REDDIT_LOGIN = ""
REDDIT_PASSWORD = ""

# Telegram

BOT_TOKEN = ""
# Integer or list of integers (User IDs)
BOT_ALLOWED_PEOPLE = []
```

## Running
### Docker
```commandline
docker-compose up -d --build
```

### No Docker
```commandline
python ./src/reddit.py
python ./src/bot.py
```

## Logging
Default path: `/data/logs/`.

File rotation happens every midnight UTC.

## Data Storage
Data is stored in `.json` object via TinyDB library.

Negatives include: can't be safely accessed from multiple threads, RAM usage.

This is a temporary measure and will be changed when something more than minor problems crop up.
import time
import logging
import logging.handlers
from sys import stdout
from datetime import datetime


try:
    from data.config import PATH_LOGS
except ImportError:
    from pathlib import Path

    PATH_LOGS = Path().cwd() / "data" / "logs"
    PATH_LOGS.mkdir(parents=True, exist_ok=True)


def get_logger(
    logger_name,
    log_format="%(created)f - %(asctime)s - %(levelname)-5s - %(message)s",
    level="info",
    stream_handler=True,
    file_handler=True,
    file_name="reddit_archiver.log",
):
    """
    Get logger.
    :param logger_name: name of the logger.
    :param log_format: format of messages.
    :param level: level of messages.
    :param stream_handler: create stream handler or not.
    :param file_handler: create file handler or not.
    :param file_name: name of log files.
    :return: logger object.
    """
    logger = logging.getLogger(logger_name)

    if level == "info":
        logger.setLevel(logging.INFO)
    elif level == "debug":
        logger.setLevel(logging.DEBUG)

    if stream_handler:
        handler = logging.StreamHandler(stdout)
        handler.setFormatter(logging.Formatter(log_format))
        logger.addHandler(handler)

    if file_handler:
        handler = logging.handlers.TimedRotatingFileHandler(PATH_LOGS / file_name, when="midnight")
        handler.setFormatter(logging.Formatter(log_format))
        logger.addHandler(handler)

    return logger


def get_split_message(message, max_size=4096, search_distance=410):
    """
    Splits message in chunks of less than or equal to max_size symbols.
    Searches for "\n\n", "\n", ". ", and " " and tries to split message by them.

    :param message: message to split.
    :param max_size: maximum size of a chunk.
    :param search_distance: numbers of symbols to search for new lines.
    :return: chunks of message.
    """
    delimiters = ["\n\n", "\n", ". ", " "]
    chunks = []
    i = 0
    index = 0

    while i < len(message):
        for delimiter in delimiters:
            index = message.rfind(
                delimiter, max(i, i + max_size - search_distance), (i + max_size)
            )

            if index != -1:
                index += len(delimiter)
                break
        if index == -1:
            index = i + max_size

        chunks.append(message[i:index])

        i = index

    return chunks


def get_ttl_hash(seconds: int = 3600):
    """
    Return the same value withing [0 to seconds] time period.

    :param seconds: maximum time to value update.
    :return: value.
    """
    return round(time.time() / seconds)


def get_number_of_seconds_before_time(time):
    """
    Get number of seconds until time.
    :param time: number of seconds into the day.
    :return: seconds until time.
    """
    current_time = datetime.now()
    current_seconds = (
        current_time.hour * 60 * 60 + current_time.minute * 60 + current_time.second
    )

    if current_seconds > time:
        difference = time + 60 * 60 * 24 - current_seconds
    else:
        difference = time - current_seconds

    return difference

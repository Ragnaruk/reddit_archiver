import requests
import requests.auth
from functools import lru_cache
from tinydb.table import Table
from tinydb import TinyDB, where
from collections import deque
from src.utils import get_logger, get_ttl_hash, get_number_of_seconds_before_time
from time import sleep


try:
    from data.config import (
        PATH_DB,
        USER_AGENT,
        HTTP_AUTH_LOGIN,
        HTTP_AUTH_PASSWORD,
        REDDIT_LOGIN,
        REDDIT_PASSWORD,
    )
except ImportError:
    from pathlib import Path

    # Path for db
    PATH_DB = Path().cwd() / "data" / "db.json"
    PATH_DB.mkdir(parents=True, exist_ok=True)

    # Bot name - "<platform>:<name>:v<version> (by /u/<username>)"
    USER_AGENT = ""

    # Reddit client id/secret
    HTTP_AUTH_LOGIN = ""
    HTTP_AUTH_PASSWORD = ""

    # Reddit login/password
    REDDIT_LOGIN = ""
    REDDIT_PASSWORD = ""


logger = get_logger("reddit_archiver", file_name="reddit_archiver.log")


@lru_cache()
def get_token(ttl_hash: int = None):
    """
    Authenticate with Reddit and receive token.

    :return: token.
    """
    del ttl_hash

    client_auth = requests.auth.HTTPBasicAuth(HTTP_AUTH_LOGIN, HTTP_AUTH_PASSWORD)
    post_data = {
        "grant_type": "password",
        "username": REDDIT_LOGIN,
        "password": REDDIT_PASSWORD,
    }
    headers = {"User-Agent": USER_AGENT}

    response = requests.post(
        "https://www.reddit.com/api/v1/access_token",
        auth=client_auth,
        data=post_data,
        headers=headers,
    )

    return response.json()["access_token"]


def is_post_in_db(db: Table, post: dict) -> bool:
    """
    Check whether db contains the post.

    :param db: TinyDB object.
    :param post: post to check.
    :return: True if post is already saved in db.
    """

    if db.search(where("permalink") == post["data"]["permalink"]):
        logger.debug('Post "{0}" is in the db.'.format(post["data"]["permalink"]))

        return True

    logger.debug('Post "{0}" is not in the db.'.format(post["data"]["permalink"]))

    return False


def add_posts_to_db(db: Table, posts: deque) -> tuple:
    """
    Add posts to db and return number of inserted and skipped entries.

    :param db: TinyDB object.
    :param posts: Deque of posts to add.
    :return: Tuple of inserted and skipped entries counters.
    """
    inserted = 0

    for post in reversed(posts):
        if not is_post_in_db(db, post):
            # db.insert(
            #     {
            #         "permalink": post["data"]["permalink"],
            #         "subreddit": post["data"]["subreddit"],
            #         "title": post["data"]["title"],
            #         "url": post["data"]["url"],
            #     }
            # )
            db.insert(post["data"])

            inserted += 1

    return inserted, len(posts) - inserted


def get_saved_posts():
    db = TinyDB(PATH_DB, sort_keys=True, indent=4).table("reddit_archive")

    # Fill out headers.
    token = get_token(get_ttl_hash())
    headers = {
        "Authorization": "bearer {}".format(token),
        "User-Agent": USER_AGENT,
    }

    # Get first batch.
    response = requests.get(
        "https://oauth.reddit.com/user/{0}/saved".format(REDDIT_LOGIN), headers=headers
    )
    received_json = response.json()
    after = received_json["data"]["after"]
    posts = deque(received_json["data"]["children"])

    all_posts = posts

    # Get next batch if all posts were added and there is a filled after field.
    while after and not is_post_in_db(db, posts[-1]):
        response = requests.get(
            "https://oauth.reddit.com/user/{}/saved?after={}".format(REDDIT_LOGIN, after),
            headers=headers,
        )
        received_json = response.json()
        after = received_json["data"]["after"]
        posts = received_json["data"]["children"]

        logger.debug("Getting new batch of posts.")

        all_posts.extend(posts)

    inserted, skipped = add_posts_to_db(db, all_posts)
    logger.info(
        "{} posts were added to the db. Skipped {} posts.".format(inserted, skipped)
    )


if __name__ == "__main__":
    wait_time = get_number_of_seconds_before_time(60 * 60 * 3)
    logger.info("Sleeping for {0} seconds until 3:00 UTC.".format(wait_time))

    sleep(wait_time)

    while True:
        get_saved_posts()

        sleep(60 * 60 * 24)

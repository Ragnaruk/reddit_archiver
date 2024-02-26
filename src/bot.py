import json
import random
from functools import wraps

from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.constants import ParseMode
from telegram.ext import (CommandHandler, ConversationHandler,
                          MessageHandler, PicklePersistence, filters, Application, ContextTypes)
from tinydb import TinyDB, where

from src.utils import get_logger, get_split_message

try:
    from data.config import (BOT_ALLOWED_PEOPLE, BOT_TOKEN, PATH_DB,
                             PATH_PERSISTENCE)
except ImportError:
    from pathlib import Path

    # Bot token
    BOT_TOKEN = ""

    # Path for db
    PATH_DB = Path().cwd() / "data" / "db.json"
    PATH_DB.mkdir(parents=True, exist_ok=True)

    # Path for persistence token
    PATH_PERSISTENCE = Path().cwd() / "data" / "persistence.pickle"

    # Integer or list of integers (User IDs)
    BOT_ALLOWED_PEOPLE = []

logger = get_logger("reddit_archiver_bot", file_name="reddit_archiver_bot.log")

def bot_step(save_step=True, reset_steps=False):
    """
    Decorator that logs user's message and records their steps.

    :param save_step: saves a step to the array of taken steps.
    :param reset_steps: empties the array of taken steps.
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            update, context = args

            message = {
                "id": update.message.from_user["id"],
                "username": update.message.from_user["username"],
                "first_name": update.message.from_user["first_name"],
                "last_name": update.message.from_user["last_name"],
                "text": update.message.text,
                "function": func.__name__,
            }

            logger.info("{}".format(json.dumps(message, ensure_ascii=False)))

            if reset_steps:
                context.user_data["steps"] = [func.__name__]
            elif save_step and context.user_data["steps"][-1] != func.__name__:
                context.user_data["steps"].append(func.__name__)

            return await func(*args, **kwargs)

        return wrapper

    return decorator


async def back(update: Update, context: ContextTypes.DEFAULT_TYPE):
    steps = context.user_data["steps"]
    methods = globals().copy()

    name = steps.pop()
    if steps:
        name = steps.pop()

    return await methods[name](update, context)


@bot_step(reset_steps=True)
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["Subreddits", "Random Post"]]
    reply_markup = ReplyKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "Welcome to Reddit Archiver Bot.",
        reply_markup=reply_markup,
        parse_mode=ParseMode.HTML,
    )

    return 1


@bot_step()
async def subreddits(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        ["Back"],
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard)

    db = TinyDB(PATH_DB, sort_keys=True, indent=4).table("reddit_archive")

    subreddits = {}
    for post in db.all():
        subreddit_name = post["subreddit"]

        if subreddit_name in subreddits:
            subreddits[subreddit_name] += 1
        else:
            subreddits[subreddit_name] = 1

    sorted_subreddits = [
        (k, v) for k, v in sorted(subreddits.items(), key=lambda item: item[0])
    ]

    message = "<b>List of subreddits:</b>\n\n"

    for key, value in sorted_subreddits:
        message += "/{0}: <b>{1}</b> posts.\n".format(key, value)

    for chunk in get_split_message(message):
        await update.message.reply_text(
            chunk,
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML,
        )

    return 1


@bot_step(save_step=False)
async def subreddit_posts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        ["Next"],
        ["Back"],
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard)

    db = TinyDB(PATH_DB, sort_keys=True, indent=4).table("reddit_archive")

    if update.message.text == "Next":
        posts = context.user_data["subreddit_posts"]
        post_number = context.user_data["subreddit_post_number"]

        if post_number >= len(posts) - 1:
            context.user_data["subreddit_post_number"] = 0
        else:
            context.user_data["subreddit_post_number"] += 1
    else:
        posts = db.search(where("subreddit") == update.message.text[1:])
        post_number = 0

        context.user_data["subreddit_posts"] = posts
        context.user_data["subreddit_post_number"] = 1

    message = (
        "<b>Subreddit:</b> r/{0}\n"
        "<b>Title:</b> {1}\n"
        "<b>Direct URL:</b> {2}\n"
        "<b>Reddit URL:</b> https://reddit.com{3}\n"
        "<b>Number:</b> {4}/{5}".format(
            posts[post_number]["subreddit"],
            posts[post_number]["title"],
            posts[post_number]["url"],
            posts[post_number]["permalink"],
            post_number + 1,
            len(posts),
        )
    )

    await update.message.reply_text(
        message,
        reply_markup=reply_markup,
        parse_mode=ParseMode.HTML,
    )

    return 1


@bot_step()
async def random_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        ["Random Post"],
        ["Back"],
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard)

    db = TinyDB(PATH_DB, sort_keys=True, indent=4).table("reddit_archive")

    post_number = random.randint(1, len(db))
    post = db.get(doc_id=post_number)

    message = (
        "<b>Subreddit:</b> r/{0}\n"
        "<b>Title:</b> {1}\n"
        "<b>Direct URL:</b> {2}\n"
        "<b>Reddit URL:</b> https://reddit.com{3}\n".format(
            post["subreddit"],
            post["title"],
            post["url"],
            post["permalink"],
        )
    )

    await update.message.reply_text(
        message,
        reply_markup=reply_markup,
        parse_mode=ParseMode.HTML,
    )

    return 1


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Goodbye.", reply_markup=ReplyKeyboardRemove())

    return ConversationHandler.END


def main():
    persistence = PicklePersistence(filepath=PATH_PERSISTENCE)
    application = Application.builder().token(token=BOT_TOKEN).persistence(persistence=persistence).build()

    conversation_handler = ConversationHandler(
        entry_points=[
            CommandHandler("start", start, filters.User(user_id=BOT_ALLOWED_PEOPLE))
        ],
        states={
            0: [
                CommandHandler("start", start, filters.User(user_id=BOT_ALLOWED_PEOPLE))
            ],
            1: [
                MessageHandler(
                    filters.User(user_id=BOT_ALLOWED_PEOPLE)
                    & filters.Regex("^(Back)$"),
                    back,
                ),
                MessageHandler(
                    filters.User(user_id=BOT_ALLOWED_PEOPLE)
                    & (filters.Regex("^/\\w+$") | filters.Regex("^(Next)$")),
                    subreddit_posts,
                ),
                MessageHandler(
                    filters.User(user_id=BOT_ALLOWED_PEOPLE)
                    & filters.Regex("^(Subreddits)$"),
                    subreddits,
                ),
                MessageHandler(
                    filters.User(user_id=BOT_ALLOWED_PEOPLE)
                    & filters.Regex("^(Random Post)$"),
                    random_post,
                ),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True,
        persistent=True,
        name="bot",
    )

    application.add_handler(handler=conversation_handler)

    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()

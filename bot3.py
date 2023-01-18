#!/usr/bin/env python
# pylint: disable=unused-argument, wrong-import-position

import logging
from typing import Dict
from os import getenv
from dotenv import load_dotenv

load_dotenv()

from telegram import __version__ as TG_VER
from kvish6_data_getter import get_kvish6_invoices

try:
    from telegram import __version_info__
except ImportError:
    __version_info__ = (0, 0, 0, 0, 0)  # type: ignore[assignment]

if __version_info__ < (20, 0, 0, "alpha", 1):
    raise RuntimeError(
        f"This example is not compatible with your current PTB version {TG_VER}. To view the "
        f"{TG_VER} version of this example, "
        f"visit https://docs.python-telegram-bot.org/en/v{TG_VER}/examples.html"
    )
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    PicklePersistence,
    filters,
)

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

CHOOSING, TYPING_REPLY, TYPING_CHOICE = range(3)

TZ_STRING = "Teudat Zehut"
CAR_PLATE_STRING = "Car Registration Number"
SEARCH_STRING = "Search"
DELETE_MY_DATA_STRING = "Delete my data"
STRINGS_DATA = [TZ_STRING, CAR_PLATE_STRING, SEARCH_STRING, DELETE_MY_DATA_STRING]

reply_keyboard = [
    [TZ_STRING, CAR_PLATE_STRING],
    [SEARCH_STRING],
    [DELETE_MY_DATA_STRING]
]
markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)


def facts_to_str(user_data: Dict[str, str]) -> str:
    """Helper function for formatting the gathered user info."""
    facts = [f"{key} - {value}" for key, value in user_data.items()]
    return "\n".join(facts).join(["\n", "\n"])


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the conversation, display any stored data and ask user for input."""
    reply_text = "Hi! I'll try to check your invoices for the toll roads in Israel \n"
    if len(context.user_data.keys()) > 1:
        reply_text += (
            f"I already know the next info about you: {', '.join(context.user_data.keys())}.\n"
            f"When you input both Teudat Zehut and Car license plate number, you can press Search"
        )
    else:
        reply_text += (
            " Please provide your Teudat Zehut and Car plate number. This information "
            " stored only in your chat and not available to developers "
        )
    await update.message.reply_text(reply_text, reply_markup=markup)

    return CHOOSING


async def regular_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Ask the user for info about the selected predefined choice."""
    text = update.message.text.lower()
    context.user_data["choice"] = text
    if context.user_data.get(text):
        reply_text = (
            f"Your {text}? I already know the following about that: {context.user_data[text]}"
        )
    else:
        reply_text = f"Your {text}? Yes, I would love to hear about that!"
    await update.message.reply_text(reply_text)

    return TYPING_REPLY


async def custom_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Ask the user for a description of a custom category."""
    await update.message.reply_text(
        'Please, use /start command and action buttons only. Currently I don\'t know how to process your message'
    )
    return CHOOSING
    #return TYPING_CHOICE


async def received_information(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Store info provided by user and ask for the next category."""
    text = update.message.text
    category = context.user_data["choice"]
    context.user_data[category] = text.lower()
    del context.user_data["choice"]

    await update.message.reply_text(
        "Neat! Just so you know, this is what you already told me:"
        f"{facts_to_str(context.user_data)}"
        "You can tell me more, or change your opinion on something.",
        reply_markup=markup,
    )

    return CHOOSING

async def delete_all(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Delete all user's info"""
    context.user_data.clear() 
    await update.message.reply_text("Your data was removed. Please use /start command to start again")
    return CHOOSING

async def show_data(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Display the gathered info."""
    await update.message.reply_text(
        f"This is what you already told me: {facts_to_str(context.user_data)}"
    )


async def search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Display the gathered info and end the conversation."""
    if "choice" in context.user_data:
        del context.user_data["choice"]

    await update.message.reply_text(
        f"I learned these facts about you: {facts_to_str(context.user_data)}Trying to search for the info!",
        reply_markup=ReplyKeyboardRemove(),
    )
    result = get_kvish6_invoices(context.user_data[TZ_STRING.lower()], context.user_data[CAR_PLATE_STRING.lower()])
    await update.message.reply_text(result)
    return ConversationHandler.END


def main() -> None:
    """Run the bot."""
    # Create the Application and pass it your bot's token.
    persistence = PicklePersistence(filepath="conversationbot")
    application = Application.builder().token(getenv('TOKEN')).persistence(persistence).build()
    
    #application.add_handler(CommandHandler("start", start))
    # Add conversation handler with the states CHOOSING, TYPING_CHOICE and TYPING_REPLY
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOOSING: [
                MessageHandler(
                    filters.Regex("^("+ TZ_STRING +"|" + CAR_PLATE_STRING + ")$"), regular_choice
                ),
                MessageHandler(
                    filters.Regex(DELETE_MY_DATA_STRING), delete_all
                ),
            ],
            TYPING_CHOICE: [
                MessageHandler(
                    filters.TEXT & ~(filters.COMMAND | filters.Regex("^Done$")), regular_choice
                )
            ],
            TYPING_REPLY: [
                MessageHandler(
                    filters.TEXT & ~(filters.COMMAND | filters.Regex("^Done$")),
                    received_information,
                )
            ],
        },
        fallbacks=[MessageHandler(filters.Regex("^" + SEARCH_STRING + "$"), search)],
        name="my_conversation",
        persistent=True,
    )

    application.add_handler(conv_handler)

    show_data_handler = CommandHandler("show_data", show_data)
    application.add_handler(show_data_handler)

    # Run the bot until the user presses Ctrl-C
    application.run_polling()


if __name__ == "__main__":
    main()
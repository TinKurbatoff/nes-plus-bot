#!/usr/bin/env python
# pylint: disable=C0116,W0613
# This program is dedicated to the public domain under the CC0 license.

"""
Simple Bot to reply to Telegram messages.
First, a few handler functions are defined. Then, those functions are passed to
the Dispatcher and registered at their respective places.
Then, the bot is started and runs until we press Ctrl-C on the command line.
Usage:
Basic Echobot example, repeats messages.
Press Ctrl-C on the command line or send a signal to the process to stop the
bot.
"""

import logging
import json
import datetime as dt

from telegram import Update, ForceReply
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

import pyjokes as pyj

try:
    with open("bot_key.txt","r") as f:
        TOKEN = f.read() 
except Exception as e:
    TOKEN = ""


# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)


# Define a few command handlers. These usually take the two arguments update and
# context.
def start(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    update.message.reply_markdown_v2(
        fr'Hi {user.mention_markdown_v2()}\!',
        reply_markup=ForceReply(selective=True),
    )


def help_command(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /help is issued."""
    update.message.reply_text('Help!')

def echo_new(update: Update, context: CallbackContext) -> None:
    """Echo the user message."""
    update.message.reply_text(f"NEW: {update.message.text}")
    return



def echo(update: Update, context: CallbackContext) -> None:
    """Echo the user message."""
    try:
        from_user = getattr(update.message,'from_user', None)
        from_user_id = getattr(from_user,'id', None)
        reply = getattr(update.message.reply_to_message,'from_user', None)
        if reply:
            ## React only to replies...
            reply_to_id = getattr(update.message.reply_to_message.from_user,'id', None)
            username = getattr(update.message.reply_to_message.from_user,'username', None)
            first_name = getattr(update.message.reply_to_message.from_user,'first_name',None)
            last_name = getattr(update.message.reply_to_message.from_user,'last_name',None)
            logger.info(f"Reply to ID:{reply_to_id}, {username} {first_name} {last_name}")
            first_char = update.message.text[0]
            commands = {"+":"Plus",
                        "-":"Minus"}
            if first_char in commands.keys():
                if reply_to_id == 1968168927:
                    # +/- to bot
                    update.message.reply_text(f"Thank you! But I am not *that* type...\nBut I like jokes.\n{pyj.get_joke()}")
                    return
                if reply_to_id == from_user_id:
                    # Self plusing
                    update.message.reply_text("That is a self-satisfaction... disgusting!")    
                    return
                # Read database
                try:
                    with open("user_data_base.json","r") as f: database = json.load(f);
                except Exception as e:
                    logger.error(f"{e}")
                    database = {1968168927:0}
                # print(database.items())
                ## Update rating
                current_rating = database.get(str(reply_to_id),0)
                last_update = int(database.get(f"{reply_to_id}_update",0))
                logger.info(f"Read: {reply_to_id}, previous rating: {current_rating} at {last_update}")
                current_rating = eval(f"{current_rating}{first_char}1")
                current_time = int(dt.datetime.utcnow().strftime('%s'))
                database[str(reply_to_id)] = current_rating
                database[f"{reply_to_id}_update"] = current_time
                difference = current_time-last_update
                if difference <60:
                    update.message.reply_text("Wait a little!")
                    return
                logger.info(f"Pause difference {current_time-last_update}")
                ## Write database 
                with open("user_data_base.json","w") as f: json.dump(database, f);
                reply_text = f"{commands[first_char]} one social credit to {first_name}. (@{username}) Total rating: {current_rating}"
                update.message.reply_text(reply_text, quote=False)
                return

    except Exception as e:
        update.message.reply_text(f"I am not feeleing well...\n")
        logger.error(f"{e}")
    return



def main() -> None:
    """Start the bot."""
    # Create the Updater and pass it your bot's token.
    updater = Updater(TOKEN)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # on different commands - answer in Telegram
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help_command))

    # on non command i.e message - echo the message on Telegram
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, echo))
    # dispatcher.add_handler(
    #     MessageHandler(            
    #         Filters.all, echo_new
    #         )
    #     )

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()

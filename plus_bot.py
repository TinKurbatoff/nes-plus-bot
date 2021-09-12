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
import os
from functools import lru_cache

from IPython.display import HTML
import re

import pandas as pd
from random import randrange

from telegram import Update, ForceReply
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

import pyjokes as pyj

try:
    with open("bot_key.txt","r") as f:
        TOKEN = f.read() 
except Exception as e:
    TOKEN = ""

USER_PANDAS_DATABASE = "users_database.pandas"
COMMANDS = {"+":"Plus",
            "-":"Minus"}

RATING_COMMANDS = {    
    "👍":"+",
    "👎":"-",
    "🙂":"+",
    "🙁":"-",
} 

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

my_style = """background-color: rgba(0, 0, 0, 0);
border-bottom-color: rgb(0, 0, 0);
border-bottom-style: none;
border-bottom-width: 0px;
border-collapse: collapse;
border-image-outset: 0px;
border-image-repeat: stretch;
border-image-slice: 100%;
border-image-source: none;
border-image-width: 1;
border-left-color: rgb(0, 0, 0);
border-left-style: none;
border-left-width: 0px;
border-right-color: rgb(0, 0, 0);
border-right-style: none;
border-right-width: 0px;
border-top-color: rgb(0, 0, 0);
border-top-style: none;
border-top-width: 0px;
box-sizing: border-box;
color: rgb(0, 0, 0);
display: table;
font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
font-size: 12px;
height: 1675px;
line-height: 20px;
margin-left: 0px;
margin-right: 0px;
margin-top: 12px;
table-layout: fixed;
text-size-adjust: 100%;
width: 700px;
-webkit-border-horizontal-spacing: 0px;
-webkit-border-vertical-spacing: 0px;
-webkit-tap-highlight-color: rgba(0, 0, 0, 0);"""


def HTML_with_style(df, style=None, random_id=None):
    from IPython.display import HTML
    import numpy as np
    import re

    df_html = df.to_html()

    if random_id is None:
        random_id = 'id%d' % np.random.choice(np.arange(1000000))

    if style is None:
        style = """
        <style>
            table#{random_id} {{color: blue}}
        </style>
        """.format(random_id=random_id)
    else:
        new_style = []
        s = re.sub(r'</?style>', '', style).strip()
        for line in s.split('\n'):
                line = line.strip()
                if not re.match(r'^table', line):
                    line = re.sub(r'^', 'table ', line)
                new_style.append(line)
        new_style = ['<style>'] + new_style + ['</style>']

        style = re.sub(r'table(#\S+)?', 'table#%s' % random_id, '\n'.join(new_style))

    df_html = re.sub(r'<table', r'<table id=%s ' % random_id, df_html)

    return style + df_html



# @lru_cache()
def read_user_database(user_database_file="users_database.pandas"):
    ## Read or create Database (pandas table)
    if os.path.isfile(user_database_file):
        users = pd.read_pickle(user_database_file, compression="gzip")
    else:
        logger.warning(f"No database {user_database_file} is found.")
        users = pd.DataFrame(columns=['user_id','username','first_name','last_name', 'rating'])
    return users

def get_user_id(username):
    users = read_user_database(user_database_file=USER_PANDAS_DATABASE)
    user_id = users.loc[users['username'] == username,'user_id']
    user_id = user_id.item() if len(user_id)>0 else None
    return user_id


def get_user_full_name(user_id):
    users = read_user_database(user_database_file=USER_PANDAS_DATABASE)
    first_name = users.loc[users['user_id'] == user_id,'first_name']
    last_name = users.loc[users['user_id'] == user_id,'last_name']
    first_name = first_name.item() if len(first_name)>0 else None
    last_name = last_name.item() if len(last_name)>0 else None
    return (first_name, last_name)

def get_user_rating(user_id=None, username=None, first_name=None):
    try:
        users = read_user_database(user_database_file=USER_PANDAS_DATABASE)
        if user_id:
            rating = users.loc[users['user_id'] == user_id,'rating']
            return rating.item() if len(rating) == 1 else 0
        elif username:
            rating = users.loc[users['username'] == username,'rating']
            return rating.item() if len(rating) == 1 else 0            
        elif first_name:
            rating = users.loc[users['first_name'] == first_name,'rating']
            return rating.item() if len(rating) == 1 else 0            
    except Exception as e:
        logger.error(f"ERROR read user database: {e}")
    return 0

def update_user_rating(user_id=None, username=None, first_name=None, rating=None):
    try:
        logger.info(f"update_user_rating| rating: {rating}")
        users = read_user_database(user_database_file=USER_PANDAS_DATABASE)
        ## Update rating        
        if (user_id in users['user_id'].to_list()):
            logger.info(f"{user_id} found, change rating")
            users.loc[users['user_id'] == user_id, 'rating'] = rating
            username = users.loc[users['user_id'] == user_id, 'username'].item()
            logger.info(f"Rating in DB updated. By {user_id}: @{username} R={rating}")

        elif (username in users['username'].to_list()):
            logger.info(f"{username} found, change rating")
            users.loc[users['username'] == username, 'rating'] =  rating
            db_user_id = users.loc[users['username'] == username, 'user_id'].item()
            logger.info(f"Rating in DB updated. By @{username}: id {db_user_id} R={rating}")
        
        elif (first_name in users['first_name'].to_list()):
            logger.info(f"{username} found, change rating")
            users.loc[users['first_name'] == first_name, 'rating'] =  rating
            db_user_id = users.loc[users['first_name'] == first_name, 'user_id'].item()
            logger.info(f"Rating in DB updated. By {first_name}: id {db_user_id} R={rating}")

        else:
            ## didn't find user
            logger.info(f"User id:{user_id}|username:{username} not found.")
            return 0

        users.to_pickle(USER_PANDAS_DATABASE, compression="gzip")
        logger.info(f"Database updated. Records: {len(users)}")
        # print(users)
        return rating
    except Exception as e:
        logger.error(f"ERROR `update_user_rating`: {e}")
    return 0            


def update_user_db(user_id=None, username=None, first_name=None, last_name=None, rating=None):
    try:
        users = read_user_database(USER_PANDAS_DATABASE)

        ## Update Database 
        if (user_id in users['user_id'].to_list()) and (username in users['username'].to_list()):
            # Already updated
            logger.info(f"{user_id} found in DB. Records: {len(users)}. No update.")
            return 
        
        elif (user_id in users['user_id'].to_list()):
            logger.info(f"{user_id} found, update user name and full name")
            users.loc[users['user_id'] == user_id, ['username','first_name','last_name']] = [username, first_name, last_name]
            logger.info(f"Database updated. Records: {len(users)} /{user_id}: @{username}, {first_name} {last_name}/")
            if rating:
                users.loc[users['user_id'] == user_id, 'rating'] = rating

        elif (username in users['username'].to_list()):
            logger.info(f"{username} found, update user name and full name")
            users.loc[users['username'] == username, ['user_id','first_name','last_name']] = [user_id, first_name, last_name]
            logger.info(f"Database updated. Records: {len(users)} /{user_id}: @{username}, {first_name} {last_name}/")
            if rating:
                users.loc[users['username'] == username, 'rating'] = rating

        else:
            users.loc[len(users),:] = [user_id, username, first_name, last_name, 0]


        users.to_pickle(USER_PANDAS_DATABASE, compression="gzip")
        logger.info(f"Database updated. Records: {len(users)} /{user_id}: @{username}, {first_name} {last_name}/")
    except Exception as e:
        logger.error(f"ERROR update user database: {e}")
    return



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

def about(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /help is issued."""
    # joke = pyj.get_joke(language = 'en', category = 'all')
    from_user = getattr(update.message,'from_user', None)
    entities = getattr(update.message,'entities', [])
    logger.info(f"/About called by {from_user}.")
    username = getattr(from_user,'username', None)
    if len(entities)>0:
        ## INFO: https://core.telegram.org/bots/api#messageentity
        logger.info(f"Entities: {update.message.entities[0]}")
        if update.message.entities[0]['type'] == 'bot_command':
            message_full = getattr(update.message,'text', None)
            message_list = message_full.split(" ")
            logger.info(f"message_list: {message_list}")
            rating = None
            m_name = None
            for text_part in message_list:
                if text_part[0] == "@":
                    m_name = text_part[1:]
                    logger.info(f"==>> Tagged: {m_name}")
                    rating = get_user_rating(username=m_name)
            if rating:
                update.message.reply_text(f'User @{m_name} has rating {rating:0,.0f}')        
                return
            elif m_name:
                update.message.reply_text(f'Who is @{m_name}, eh?')
                return
                                    
    if username == 'banknote2000':
        users = read_user_database(USER_PANDAS_DATABASE)
        # joke = HTML_with_style(users, '<style>table {{{}}}</style>'.format(my_style))
        # split dataframe on parts by 30 records
        for part in range(1, len(users)//30+2):
            from_line = part*30-30
            to_line = part*30
            logger.info(f"==== PART {part} ====")
            logger.info(f"lines from {from_line} to {to_line}")
            users_part = users.iloc[from_line:to_line,:].to_string(header=True, index=False)
            update.message.reply_text(f"==== PART {part} ====\nfrom {from_line} to {to_line}\n{users_part}")
        return
    else:
        joke = "No joke. It is not funny."
        update.message.reply_text(f'I like jokes.\n{joke}')
        return

def change(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /help is issued."""
    # joke = pyj.get_joke(language = 'en', category = 'all')
    try:
        reply_list = getattr(update.message,'from_user', None)
        logger.info(f"/Change called by {reply_list}.")
        caller_username = getattr(reply_list,'username', None)
        if caller_username == 'banknote2000':
            # update.message.reply_text(f'Change rating.\n')
            if len(update.message.entities)>0:
                ## INFO: https://core.telegram.org/bots/api#messageentity
                logger.info(f"Entities: {update.message.entities[0]}")
                if update.message.entities[0]['type'] == 'bot_command':
                    message_full = getattr(update.message,'text', None)
                    message_list = message_full.split(" ")
                    logger.info(f"message_list: {message_list}")
                    new_rating = None
                    for text_part in message_list:
                        if text_part[0] == "@":
                            m_name = text_part[1:]
                            logger.info(f" Tagged: {m_name}")
                            for number_or_not in message_list:
                                if number_or_not.isdigit():
                                    new_rating = int(number_or_not)
                            break
                    if new_rating:
                        update.message.reply_text(f'Change rating of {m_name} to {new_rating}.\n')
                        update_user_rating(username=m_name, rating=new_rating)
                    else:
                        update.message.reply_text("Use: /Change @user <rating>")
                return
        else:
            joke = "It will not change."
        update.message.reply_text(f'I like jokes.\n{joke}')
    except Exception as e:
        logger.error(f"Rating /change function error: {e}")
    return 

def echo_new(update: Update, context: CallbackContext) -> None:
    """Echo the user message."""
    update.message.reply_text(f"NEW: {update.message.text}")
    return

def get_gif_data():
    files = []
    for file in os.listdir("."):
        if file.endswith(".gif"):
            files.append(file)
    new_gif = files[randrange(len(files))] 
    logger.info(f"-== Used gif file: {new_gif}")
    animation = open(new_gif, 'rb').read()    
    return animation


def echo_gif(update: Update, context: CallbackContext) -> None:
    """Echo the user message."""

    context.bot.sendAnimation(chat_id=update.message.chat_id,
               animation=get_gif_data(),
               caption='That is your gif!',
               # parse_mode=ParseMode.MARKDOWN
               )
    print("GIF!")
    return    

def update_rating_routine(update, context, first_char, from_user_id, reply_to_id=None, username=None, first_name=None, last_name=None):
    current_rating = 0
    commands = COMMANDS
    try:
        if reply_to_id == None:
            # current_rating = get_user_rating(user_id=None, username=username, first_name=None)
            reply_to_id = get_user_id(username=username)
            first_name, last_name = get_user_full_name(reply_to_id)        

        if reply_to_id == 1968168927:
            # +/- to bot
            update.message.reply_text(f"Thank you! I am not *that* type...\nBut I like jokes.\n{pyj.get_joke()}")
            return
        if reply_to_id == from_user_id:
            # Self "plus"-ing
            joke = pyj.get_joke(language = 'en', category = 'chuck')
            update.message.reply_text(f"I like you too...Are you Chuck?\n{joke}")    
            return
        # Read database
        try:
            with open("user_data_base.json","r") as f: database = json.load(f);
        except Exception as e:
            logger.error(f"{e}")
            database = {1968168927:0}
        # print(database.items())
        
        ## Update rating
        # current_rating = database.get(str(reply_to_id),0)            
        current_rating = get_user_rating(user_id=reply_to_id, username=None, first_name=None)
        logger.info(f"Current rating readed: {current_rating} ")
        # last_update = int(database.get(f"{reply_to_id}_update",0))
        logger.info(f"Read: {reply_to_id}, previous rating: {current_rating}")
        current_rating = eval(f"{current_rating}{first_char}1")
        
        ## —— Make a delay 
        current_time = int(dt.datetime.utcnow().strftime('%s')) # Time Now
        try:
            with open("recent_appreciations.json", "r+") as f: recents = json.load(f);
        except Exception as e:
            logger.error(f"{e}")
            recents = {}
        ## filter out old appreciations (>60 sec)
        new_recents = {k:v for k,v in recents.items() if (current_time-int(k)) <= 60}
        
        # Search for a users pair in recent appreiations
        for k,v in new_recents.items():
            if (str(from_user_id) in v.keys()) and (reply_to_id == v.get(str(from_user_id), None)):
                update.message.reply_text("Wait a little!")
                logger.info(f"Not updated: {from_user_id}->{reply_to_id} => Pause difference: {current_time-int(k)}")
                return

        ## add a new appreciation to stack
        if current_time not in new_recents.keys():
            new_recents[current_time] = {}
        new_recents[current_time][from_user_id] = reply_to_id
        with open("recent_appreciations.json", "w") as f: recents = json.dump(new_recents,f);
        ## ——
        
        ## Write database if everything is okay!
        database[str(reply_to_id)] = current_rating ## update new rating
        update_user_rating(user_id=reply_to_id, username=None, rating=current_rating)
        with open("user_data_base.json","w") as f: json.dump(database, f);    
        current_rating = int(current_rating)
        reply_text = f"{commands[first_char]} one social credit to {first_name}. (@{username}) Total rating: {current_rating}"
        first_name, last_name = get_user_full_name(user_id=reply_to_id)
        update_user_db(user_id=reply_to_id, username=username, first_name=first_name, last_name=last_name)
        if current_rating % 25 == 0:
            # Show with gif
            context.bot.sendAnimation(chat_id=update.message.chat_id,
               animation=get_gif_data(),
               caption=reply_text,)
        else: 
            ## Routine as usual
            update.message.reply_text(reply_text, quote=False)
    except Exception as e:
        logger.error(f"Rating update routine error: {e}")
    return 


def echo(update: Update, context: CallbackContext) -> None:
    """Echo the user message."""
    commands = COMMANDS
    try:
        from_user = getattr(update.message,'from_user', None)
        from_user_id = getattr(from_user,'id', None)
        if not getattr(update,'message', None):
            logger.warning("Empty message")
            return
        reply = getattr(update.message.reply_to_message,'from_user', None)
        with open("telgram_messages.txt", "a") as f:
            f.write(f"From_user:{from_user} from_user_id:{from_user_id} | Chat: '{update.message.chat['title']}' TEXT:'{update.message.text}'\n")
        # logger.info(f"echo, from_user:{from_user} from_user_id:{from_user_id} TEXT:{update.message.text}")
        if len(update.message.entities)>0:
            ## INFO: https://core.telegram.org/bots/api#messageentity
            logger.info(update.message.entities[0])
            if update.message.entities[0]['type'] == 'mention':
                x,y = update.message.entities[0]['offset'],update.message.entities[0]['length']
                m_name = update.message.text[x:x+y]
                logger.info(f" Tagged: {m_name}")
                message_text = getattr(update.message,'text',None)
                first_char = message_text[0]
                if first_char in RATING_COMMANDS.keys():
                    first_char = RATING_COMMANDS[first_char]
                if (message_text) and (first_char in commands.keys()):
                    logger.info("+ @user appreciation detected...")
                    update_rating_routine(update, context, first_char=first_char, 
                            from_user_id=from_user_id, 
                            reply_to_id=None, 
                            username=m_name[1:])
                    ## + @user way of appreciataion
            return

            # for k in dir(update.message.entities[0]):
            #     if k[0] != "_":
            #         logger.info(f'{k}:{getattr(update.message.entities,k, "<▒▒▒▒▒▒▒▒▒>")}')
        if reply:
            ## React only to replies...
            reply_to_id = getattr(update.message.reply_to_message.from_user,'id', None)
            username = getattr(update.message.reply_to_message.from_user,'username', None)
            first_name = getattr(update.message.reply_to_message.from_user,'first_name',None)
            last_name = getattr(update.message.reply_to_message.from_user,'last_name',None)
            update_user_db(user_id=reply_to_id, username=username, first_name=first_name, last_name=last_name)
            logger.info(f"Reply to ID:{reply_to_id}, @{username} Name: {first_name} {last_name}")
            first_char = update.message.text[0]
            if first_char in RATING_COMMANDS.keys():
                first_char = RATING_COMMANDS[first_char]            
            if first_char in commands.keys():
                update_rating_routine(update, first_char=first_char, 
                            from_user_id=from_user_id, 
                            reply_to_id=reply_to_id, 
                            username=username, 
                            first_name=first_name, last_name=last_name)
                # update_rating_routine(update, first_char, from_user_id, reply_to_id)
                return
        else:
            logger.info("Note a reply.")

    except Exception as e:
        update.message.reply_text(f"I am not feeling well...\n")
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
    dispatcher.add_handler(CommandHandler("about", about))
    dispatcher.add_handler(CommandHandler("change", change))
    dispatcher.add_handler(CommandHandler("help", help_command))
    dispatcher.add_handler(CommandHandler("gif", echo_gif))

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

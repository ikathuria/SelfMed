import re
import os
import pandas as pd

from flask import Flask, request
import telegram

from telebot.credentials import bot_token, bot_user_name, URL
from telebot.prediction import *

# # ####################################################################################
app = Flask(__name__)

global bot
global TOKEN
global updater

TOKEN = bot_token
bot = telegram.Bot(token=TOKEN)

df = pd.read_excel("/home/ikathuria/selfmed/static/final data.xlsx", index_col=0)
disease1 = [i for i in df['disease'].to_list() if isinstance(i, str)]
disease2 = [i for i in df['synonym_disease'].to_list() if isinstance(i, str)]
disease3 = [i for i in df['synonym_disease2'].to_list() if isinstance(i, str)]
remedies = df['remedies'].to_list()
diseases_overview = [i for i in df['overview'].to_list() if isinstance(i, str)]


DIS_DICT = {}
for i in range(len(disease1)):
    try:
        DIS_DICT[disease1[i]] = preprocess_pipe(diseases_overview[i])
    except:
        pass

for i in range(len(disease2)):
    try:
        DIS_DICT[disease2[i]] = preprocess_pipe(diseases_overview[i])
    except:
        pass

for i in range(len(disease3)):
    try:
        DIS_DICT[disease3[i]] = preprocess_pipe(diseases_overview[i])
    except:
        pass


# # ####################################################################################
@app.route('/')
def index():
    return 'SelfMed Chatbot.'


@app.route('/{}'.format(TOKEN), methods=['POST'])
def respond():
    # retrieve the message in JSON and then transform it to Telegram object
    update = telegram.Update.de_json(request.get_json(force=True), bot)

    chat_id = update.message.chat.id
    msg_id = update.message.message_id

    # Telegram understands UTF-8, so encode text for unicode compatibility
    text = update.message.text.encode('utf-8').decode().lower()

    # for debugging
    print("got text message :", text)

    # welcoming message ##############################################################
    if text == "/start":
        # print the welcoming message
        bot_welcome = """
Hello 🙋🏽‍♂
This is SelfMed, a self diagnosis and remedy chatbot developed by Ishani Kathuria & Kamad Saxena to provide free healthcare advice.
How are you feeling today?
/symptoms - Find disease by describing your symptoms
/remedy - Find remedies to conditions you already know about

📞 National health Helpline: 1800-180-1104 | Ambulance: 102
        """

        # send the welcoming message
        bot.sendMessage(
            chat_id=chat_id, text=bot_welcome, reply_to_message_id=msg_id
        )

    # help text #######################################################################
    elif text == "/help":
        bot_welcome = """
/symptoms - Find disease by describing your symptoms
/remedy - Find remedies to conditions you already know about
        """

        bot.sendMessage(
            chat_id=chat_id, text=bot_welcome, reply_to_message_id=msg_id
        )

    # check symtoms ####################################################################
    elif text == "/symptoms":
        bot_welcome = """
Enter your symptoms
        """

        bot.sendMessage(
            chat_id=chat_id, text=bot_welcome, reply_to_message_id=msg_id
        )

        text = update.message.text.encode('utf-8').decode().lower()
        text = preprocess_pipe(text)
        predict_disease(text, DIS_DICT)


    # find remedy ####################################################################
    elif text == "/remedy":
        bot_welcome = """
Enter your medical condition / disease
        """

        bot.sendMessage(
            chat_id=chat_id, text=bot_welcome, reply_to_message_id=msg_id
        )

    elif text in disease1:
        rem = remedies[disease1.index(text)].split('\n')

        for i in rem:
            bot.sendMessage(
                chat_id=chat_id, text=i, reply_to_message_id=msg_id
            )

    elif text in disease2:
        rem = remedies[disease2.index(text)].split('\n')

        for i in rem:
            bot.sendMessage(
                chat_id=chat_id, text=i, reply_to_message_id=msg_id
            )

    elif text in disease3:
        rem = remedies[disease3.index(text)].split('\n')

        for i in rem:
            bot.sendMessage(
                chat_id=chat_id, text=i, reply_to_message_id=msg_id
            )

    else:
        bot_welcome = """
/symptoms - Find disease by describing your symptoms
/remedy - Find remedies to conditions you already know about
        """

        bot.sendMessage(
            chat_id=chat_id, text=bot_welcome, reply_to_message_id=msg_id
        )

    return 'ok'


@app.route('/setwebhook', methods=['GET', 'POST'])
def set_webhook():
    # we use the bot object to link the bot to our app which lives
    # in the link provided by URL
    print(URL + TOKEN)
    s = bot.setWebhook(URL + TOKEN)
    # something to let us know things work
    if s:
        return "webhook setup ok"
    else:
        return "webhook setup failed"


if __name__ == '__main__':
    # note the threaded arg which allow
    # your app to have more than one thread
    app.run(threaded=True)

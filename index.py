import re
import os
import git
import hmac
import hashlib
import pandas as pd

from flask import Flask, request
import telegram
from telebot.credentials import bot_token, bot_user_name, URL
# from twilio.twiml.messaging_response import MessagingResponse

# # ####################################################################################
app = Flask(__name__)


global bot
global TOKEN
global W_KEY

TOKEN = bot_token
bot = telegram.Bot(token=TOKEN)
W_KEY = os.getenv("SECRET_KEY")


# df = pd.read_csv("/home/ikathuria/selfmed/static/mayo data.csv", index_col=0)
# df['remedies'] = df['remedies'].apply(
#     lambda x: x.replace('[', '').replace(']', '').replace(
#         "\"", '').replace("\'", '') if type(x) != float else ''
# )

# upper_disease = df.disease.tolist()
# lower_disease = df.lower_disease.tolist()
# remedies = df.remedies.apply(lambda x: x.split(', ') if type(x) != float else '').tolist()


# # ####################################################################################
def is_valid_signature(x_hub_signature, data, private_key):
    # x_hub_signature and data are from the webhook payload
    # private key is the webhook secret
    hash_algorithm, github_signature = x_hub_signature.split('=', 1)
    algorithm = hashlib.__dict__.get(hash_algorithm)
    encoded_key = bytes(private_key, 'latin-1')
    mac = hmac.new(encoded_key, msg=data, digestmod=algorithm)
    return hmac.compare_digest(mac.hexdigest(), github_signature)


@app.route('/')
def index():
    return 'SelfMed Chatbot.'


@app.route('/update_server', methods=['POST'])
def webhook():
    if request.method == 'POST':
        x_hub_signature = request.headers.get('X-Hub-Signature')
        if not is_valid_signature(x_hub_signature, request.data, W_KEY):
            return 'Wrong event type', 400

        repo = git.Repo('https://github.com/ikathuria/SelfMed.git')
        origin = repo.remotes.origin
        origin.pull()
        return 'Updated PythonAnywhere successfully', 200

    else:
        return 'Wrong event type', 400


@app.route('/{}'.format(TOKEN), methods=['POST'])
def respond():
    # retrieve the message in JSON and then transform it to Telegram object
    update = telegram.Update.de_json(request.get_json(force=True), bot)

    chat_id = update.message.chat.id
    msg_id = update.message.message_id

    # Telegram understands UTF-8, so encode text for unicode compatibility
    text = update.message.text.encode('utf-8').decode()

    # for debugging
    print("got text message :", text)

    # the first time you chat with the bot AKA the welcoming message
    if text == "/start":
        # print the welcoming message
        bot_welcome = """
       Hello 🙋🏽‍♂, \nThis is SelfMed, a self diagnosis and remedy chatbot developed by Ishani Kathuria & Kamad Saxena to provide free healthcare advice.\n📞 National health Helpline: 1800-180-1104 | \n Ambulance: 102 \nHow are you feeling today? \n*1.* Check my symptoms. \n*2.* Find remedy for my condition.
       """
        # send the welcoming message
        bot.sendMessage(
            chat_id=chat_id, text=bot_welcome, reply_to_message_id=msg_id
        )

    else:
        try:
            # clear the message we got from any non alphabets
            text = re.sub(r"\W", "_", text)

            # create the api link for the avatar based on http://avatars.adorable.io/
            url = "https://api.adorable.io/avatars/285/{}.png".format(
                text.strip()
            )

            # reply with a photo to the name the user sent,
            # note that you can send photos by url and telegram will fetch it for you
            bot.sendPhoto(chat_id=chat_id, photo=url,
                          reply_to_message_id=msg_id)

        except Exception:
            # if things went wrong
            bot.sendMessage(
                chat_id=chat_id,
                text="There was a problem in the name you used, please enter different name",
                reply_to_message_id=msg_id
            )

    return 'ok'


@app.route('/setwebhook', methods=['GET', 'POST'])
def set_webhook():
    # we use the bot object to link the bot to our app which live
    # in the link provided by URL
    s = bot.setWebhook('{URL}{HOOK}'.format(URL=URL, HOOK=TOKEN))
    # something to let us know things work
    if s:
        return "webhook setup ok"
    else:
        return "webhook setup failed"


# @app.route('/bot', methods=['POST'])
# def bot():
#     incoming_msg = request.values.get('Body', '').lower()
#     resp = MessagingResponse()
#     msg = resp.message()
#     responded = False

#     greeting = [
#         'hi', 'hey', 'heya', 'hello', 'sup',
#         'whats up', 'bonjour', 'hola', 'menu'
#     ]

#     if incoming_msg in greeting:
#         text = "Hello 🙋🏽‍♂, \nThis is SelfMed, a self diagnosis and remedy chatbot developed by Ishani Kathuria & Kamad Saxena to provide free healthcare advice.\n📞 National health Helpline: 1800-180-1104 | \n Ambulance: 102 \nHow are you feeling today? \n*1.* Check my symptoms. \n*2.* Find remedy for my condition."
#         msg.body(text)

#         responded = True

#     if incoming_msg == '1':
#         text = "Please type in your symptoms in separate lines to begin."
#         msg.body(text)

#         responded = True

#     if incoming_msg == '2':
#         text = "Please type in the disease you want a remedy for."
#         msg.body(text)

#         responded = True

#     if incoming_msg in lower_disease:
#         text = remedies[lower_disease.index(incoming_msg)][:5]
#         text = "\n".join(text)
#         msg.body(text)

#         responded = True

#     if responded == False:
#         msg.body("Sorry! I couldn't understand. Please try again.")

#     return str(resp)


if __name__ == '__main__':
    # note the threaded arg which allow
    # your app to have more than one thread
    app.run(threaded=True)

import pickle

from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse

app = Flask(__name__)


def load_pickle(filename):
    with open(filename, "rb" ) as f:
        file = pickle.load(f)
    return file


@app.route("/")
def hello():
    return "Hello World!"


@app.route('/bot', methods=['POST'])
def bot():
    incoming_msg = request.values.get('Body', '').lower()
    resp = MessagingResponse()
    msg = resp.message()
    responded = False

    greeting = [
        'hi', 'hey', 'heya', 'hello', 'sup',
        'whats up', 'bonjour', 'hola', 'menu'
    ]

    if incoming_msg in greeting:
        text = f"Hello 🙋🏽‍♂, \nThis is SelfMed, a self diagnosis and remedy chatbot developed by Ishani Kathuria & Kamad Saxena to provide free healthcare advice.\n📞 National health Helpline: 1800-180-1104 | \n Ambulance: 102 \nHow are you feeling today? \n*1.* Check my symptoms. \n*2.* Find remedy for my condition."
        msg.body(text)
        responded = True

    if incoming_msg == 1:
        text = "Please type in your symptoms in separate lines to begin."
        msg.body(text)
        responded = True

    if incoming_msg == 2:
        text = "Please type in the disease you want a remedy for."
        msg.body(text)
        responded = True

    if responded == False:
        msg.body("Sorry! I couldn't understand. Please try again.")

    return str(resp)

if __name__ == "__main__":
    app.run()

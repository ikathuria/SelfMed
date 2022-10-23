import json
import requests
import numpy as np
import pandas as pd
import pickle

from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse

app = Flask(__name__)


df = pd.read_csv("/home/ikathuria/selfmed/static/mayo data.csv", index_col=0)
df['remedies'] = df['remedies'].apply(
    lambda x: x.replace('[', '').replace(']', '').replace(
        "\"", '').replace("\'", '') if type(x) != float else ''
)

upper_disease = df.disease.tolist()
lower_disease = df.lower_disease.tolist()
remedies = df.remedies.apply(lambda x: x.split(
    ', ') if type(x) != float else '').tolist()


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
        text = "Hello 🙋🏽‍♂, \nThis is SelfMed, a self diagnosis and remedy chatbot developed by Ishani Kathuria & Kamad Saxena to provide free healthcare advice.\n📞 National health Helpline: 1800-180-1104 | \n Ambulance: 102 \nHow are you feeling today? \n*1.* Check my symptoms. \n*2.* Find remedy for my condition."
        msg.body(text)

        responded = True

    if incoming_msg == '1':
        text = "Please type in your symptoms in separate lines to begin."
        msg.body(text)

        responded = True

    if incoming_msg == '2':
        text = "Please type in the disease you want a remedy for."
        msg.body(text)

        responded = True

    if incoming_msg in lower_disease:
        text = remedies[lower_disease.index(incoming_msg)][:5]
        text = "\n".join(text)
        msg.body(text)

        responded = True

    if responded == False:
        msg.body("Sorry! I couldn't understand. Please try again.")

    return str(resp)


if __name__ == "__main__":
    app.run()

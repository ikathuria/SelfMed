import os
import re
import logging
import pandas as pd
from typing import Dict
from dotenv import load_dotenv

# telegram API
from telegram import __version__ as TG_VER
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    Update
)
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    CallbackQueryHandler,
    PicklePersistence,
    filters,
)

try:
    from telegram import __version_info__
except ImportError:
    __version_info__ = (0, 0, 0, 0, 0)

if __version_info__ < (20, 0, 0, "alpha", 1):
    raise RuntimeError(
        f"This example is not compatible with your current PTB version {TG_VER}. To view the "
        f"{TG_VER} version of this example, "
        f"visit https://docs.python-telegram-bot.org/en/v{TG_VER}/examples.html"
    )

# custom functions
from static.prediction import *
from static.credentials import *


# # ####################################################################################
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.DEBUG
)
logger = logging.getLogger(__name__)
load_dotenv()


# # ####################################################################################
CHOOSING, USER_SET, AGE, GENDER, LANG = range(5)
REMEDY, DISEASE, DIS_REMEDY = range(100, 103)

settings_keyboard = [
    ["Age", "Gender", "Language"],
    ["Done"]
]
settings_markup = ReplyKeyboardMarkup(
    settings_keyboard,
    one_time_keyboard=True
)

# # # ####################################################################################
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global diseases
    global remedies

    bot_welcome = """
Hello 🙋🏽‍♂
This is SelfMed, a self diagnosis and remedy chatbot developed by Ishani Kathuria & Kamad Saxena to provide free healthcare advice.
/help - learn the functions of the chatbot
/symptoms - find your disease by describing your symptoms
/remedy - find remedies to conditions you have
/settings - change default user information

📞 National health Helpline: 1800-180-1104
🚑 Ambulance: 102
"""
    if context.user_data.get("language") == "hindi":
        diseases = df.hindi_disease.to_list()
        remedies = df.hindi_remedies.to_list()

        bot_welcome = """
नमस्ते 🙋🏽‍♂
यह SelfMed है, जो ईशानी कथूरिया और कामद सक्सेना द्वारा विकसित एक सेल्फ डायग्नोसिस और उपाय चैटबॉट है, जो मुफ्त स्वास्थ्य सलाह प्रदान करता है।
/help - चैटबॉट के कार्यों को जानें
/symptoms - अपने लक्षणों का वर्णन करके अपने रोग का पता लगाएं
/remedy - आपके पास मौजूद स्थितियों के लिए उपचार खोजें
/settings - डिफ़ॉल्ट उपयोगकर्ता जानकारी बदलें

📞 राष्ट्रीय स्वास्थ्य हेल्पलाइन: 1800-180-1104
🚑 एम्बुलेंस: 102
    """

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=bot_welcome
    )


# # # ####################################################################################
async def settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Ask the user for info about the selected predefined choice.
    """

    text = "Update your personal details"
    if context.user_data.get("language") == "hindi":
        text = "अपनी व्यक्तिगत जानकारी अपडेट करें"

    await update.message.reply_text(
        text,
        reply_markup=settings_markup,
    )

    return CHOOSING


async def set_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Set user's details
    """

    text = update.message.text

    if text == "Age":
        reply = "Please enter your age"
        if context.user_data.get("language") == "hindi":
            reply = "कृपया अपनी उम्र दर्ज करें"

        await update.message.reply_text(
            reply,
            reply_markup=ReplyKeyboardRemove(),
        )

        return AGE

    elif text == "Gender":
        reply = "Please choose your gender"
        keyboard = [
            [InlineKeyboardButton("Male", callback_data="Male")],
            [InlineKeyboardButton("Female", callback_data="Female")],
            [InlineKeyboardButton("Other", callback_data="Other")]
        ]
        if context.user_data.get("language") == "hindi":
            reply = "कृपया अपना लिंग चुनें"
            keyboard = [
                [InlineKeyboardButton("पुरुष", callback_data="Male")],
                [InlineKeyboardButton("महिला", callback_data="Female")],
                [InlineKeyboardButton("दूसरे", callback_data="Other")]
            ]

        markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            reply,
            reply_markup=markup,
        )

        return GENDER

    elif text == "Language":
        reply = "Please choose your preferred language"
        if context.user_data.get("language") == "hindi":
            reply = "कृपया अपनी पसंदीदा भाषा चुनें"

        keyboard = [
            [InlineKeyboardButton('English', callback_data="English")],
            [InlineKeyboardButton('हिन्दी', callback_data="Hindi")]
        ]
        markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            reply,
            reply_markup=markup,
        )

        return LANG

    else:
        await update.message.reply_text(
            f"I learned these facts about you: {facts_to_str(context.user_data)}",
            reply_markup=ReplyKeyboardRemove(),
        )

        return ConversationHandler.END


async def handle_age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Set user's age
    """

    text = int(update.message.text)
    context.user_data["age"] = text

    thank_you = "Your age is now set to " + str(text)
    if context.user_data.get("language") == "hindi":
        thank_you = eng2hi(thank_you)

    await update.message.reply_text(
        text=thank_you,
        reply_markup=settings_markup,
    )

    return CHOOSING


async def handle_gender(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Set user's gender
    """

    query = update.callback_query
    await query.answer()

    text = query.data
    context.user_data["gender"] = text.lower()

    thank_you = "Your gender is now set as " + text
    if context.user_data.get("language") == "hindi":
        thank_you = eng2hi(thank_you)

    await update.callback_query.message.reply_text(
        thank_you,
        reply_markup=settings_markup,
    )

    return CHOOSING


async def handle_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Store user's default language.
    """
    global diseases
    global remedies

    query = update.callback_query
    await query.answer()

    text = query.data

    context.user_data["language"] = text.lower()

    thank_you = "Your chosen language is now English."
    if context.user_data.get("language") == "hindi":
        thank_you = "आपकी चुनी हुई भाषा अब हिंदी है।"
        diseases = df.hindi_disease.to_list()
        remedies = df.hindi_remedies.to_list()
    else:
        diseases = df.disease.to_list()
        remedies = df.remedies.to_list()

    await update.callback_query.message.reply_text(
        text=thank_you,
        reply_markup=settings_markup,
    )

    return CHOOSING


# # # ####################################################################################
async def get_condition(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bot_welcome = "Please choose the condition you want remedies for"

    if context.user_data.get("language") == "hindi":
        bot_welcome = eng2hi(bot_welcome)

    reply_keyboard = [[i] for i in diseases]
    markup = ReplyKeyboardMarkup(
        reply_keyboard,
        one_time_keyboard=True,
    )

    await update.message.reply_text(
        text=bot_welcome,
        reply_markup=markup
    )

    return REMEDY


async def give_remedy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    dis = update.message.text.lower()
    rem = remedies[diseases.index(dis)].split('\n')

    for i in rem:
        if not check_image_url(i):
            await update.message.reply_text(
                i,
                reply_markup=ReplyKeyboardRemove(),
            )
        else:
            await update.message.reply_photo(photo=i)

    return ConversationHandler.END


# # # ####################################################################################
async def get_symptoms(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bot_welcome = "Please give a brief of your symptoms"

    if context.user_data.get("language") == "hindi":
        bot_welcome = eng2hi(bot_welcome)

    await update.message.reply_text(
        text=bot_welcome
    )

    return DISEASE


async def give_disease(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower()
    reply = "Processing your symptoms..."

    if context.user_data.get("language") == "hindi":
        reply = eng2hi(reply)

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=reply
    )

    preds = combine_functions(
        text, hin=context.user_data.get("language", False)
    )

    keyboard = []
    for res in preds:
        for dis, score in res.items():
            temp = [InlineKeyboardButton(
                "%s %.4f" %(dis, score),
                callback_data=dis
            )]
            keyboard.append(temp)
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "Please choose the most suitable disease:",
        reply_markup=reply_markup
    )

    return DIS_REMEDY


async def give_disease_remedy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    dis = query.data

    reply = "Please submit some more symptoms for better results..."
    if context.user_data.get("language") == "hindi":
        reply = eng2hi(reply)

    if 'none' in dis:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=reply
        )

        return DISEASE

    for i in remedies[diseases.index(dis)].split('\n'):
        if not check_image_url(i):
            await update.callback_query.message.reply_text(
                i,
                reply_markup=ReplyKeyboardRemove()
            )
        else:
            await update.callback_query.message.reply_photo(photo=i)

    return ConversationHandler.END


# # # ####################################################################################
def facts_to_str(user_data: Dict[str, str]):
    """
    Helper function for formatting the gathered user info.
    """

    facts = [f"{key} - {value}" for key, value in user_data.items()]
    return "\n".join(facts).join(["\n", "\n"])


async def done(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Display the gathered info and ends the settings conversation.
    """
    
    reply = f"I learned these facts about you: {facts_to_str(context.user_data)}"
    if context.user_data.get("language") == "hindi":
        reply = eng2hi(reply)

    await update.message.reply_text(
        reply,
        reply_markup=ReplyKeyboardRemove(),
    )

    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Cancels and ends the conversation.
    """

    reply = "Thank you, bye! Stay safe."
    if context.user_data.get("language") == "hindi":
        reply = eng2hi(reply)

    await update.message.reply_text(
        reply,
        reply_markup=ReplyKeyboardRemove()
    )

    return ConversationHandler.END


def main():
    """
    Run the bot.
    """

    # persistence = PicklePersistence(filepath="conversationbot")
    application = Application.builder().token(
        TOKEN
    ).build()

    start_handler = CommandHandler(["start", "help"], start)
    application.add_handler(start_handler)

    settings_handler = ConversationHandler(
        entry_points=[CommandHandler("settings", settings)],
        states={
            CHOOSING: [MessageHandler(
                filters=filters.TEXT,
                callback=set_info
            )],
            AGE: [MessageHandler(
                filters=filters.Regex(r'\d+'),
                callback=handle_age
            )],
            GENDER: [CallbackQueryHandler(handle_gender)],
            LANG: [CallbackQueryHandler(handle_language)],
        },
        fallbacks=[MessageHandler(filters.TEXT, done)]
    )
    application.add_handler(settings_handler)

    remedy_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("remedy", get_condition)],
        states={
            REMEDY: [MessageHandler(
                filters=filters.TEXT,
                callback=give_remedy
            )],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    application.add_handler(remedy_conv_handler)

    symptoms_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("symptoms", get_symptoms)],
        states={
            DISEASE: [MessageHandler(
                filters=filters.TEXT,
                callback=give_disease
            )],
            DIS_REMEDY: [CallbackQueryHandler(give_disease_remedy)]
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    application.add_handler(symptoms_conv_handler)

    application.run_polling()
    # application.run_webhook(
    #     listen="0.0.0.0",
    #     port=int(PORT),
    #     url_path=TOKEN,
    #     webhook_url=URL+TOKEN
    # )


if __name__ == '__main__':
    main()

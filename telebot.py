import os
import logging
import pandas as pd
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
    filters,
)

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

# custom functions
from static.prediction import *

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)
load_dotenv()


# # ####################################################################################
df = pd.read_excel("static/datasets/final data.xlsx")
diseases = [i for i in df['disease'].to_list()]
remedies = df['remedies'].to_list()

DIS_DICT = {}
for i in range(len(diseases)):
    try:
        DIS_DICT[diseases[i]] = preprocess_pipe(diseases_overview[i])
    except:
        pass


# # ####################################################################################
global TOKEN
global URL

TOKEN = os.environ.get('TOKEN')
PORT = int(os.environ.get('PORT', 8443))
URL = os.environ.get('URL')

REMEDY = 0
DISEASE = 1
DIS_REMEDY = 2


# # # ####################################################################################
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bot_welcome = """
Hello 🙋🏽‍♂
This is SelfMed, a self diagnosis and remedy chatbot developed by Ishani Kathuria & Kamad Saxena to provide free healthcare advice.
How are you feeling today?
/symptoms - Find disease by describing your symptoms
/remedy - Find remedies to conditions you already know about

📞 National health Helpline: 1800-180-1104 | Ambulance: 102
"""

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=bot_welcome
    )


async def get_condition(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bot_welcome = """
Please choose the condition you want remedies for
"""

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
    text = update.message.text.lower()
    rem = remedies[diseases.index(text)].split('\n')

    for i in rem:
        await update.message.reply_text(
            i,
            reply_markup=ReplyKeyboardRemove(),
        )

    return ConversationHandler.END


async def get_symptoms(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bot_welcome = """
Please give a brief of your symptoms
"""

    await update.message.reply_text(
        text=bot_welcome
    )

    return DISEASE


async def give_disease(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower()

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Processing your symptoms..."
    )

    keyboard = []
    preds = combine_functions(text)
    print(preds)

    for res in preds:
        for dis, score in res.items():
            temp = [InlineKeyboardButton(
                    "%s %.4f" %(dis, score), callback_data=dis
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

    res = query.data
    for i in remedies[diseases.index(res)].split('\n'):
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=i
        )

    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancels and ends the conversation."""

    await update.message.reply_text(
        "Bye! Stay safe, wear a mask.",
        reply_markup=ReplyKeyboardRemove()
    )

    return ConversationHandler.END


def main():
    """Run the bot."""
    application = Application.builder().token(TOKEN).build()

    start_handler = CommandHandler("start", start)
    application.add_handler(start_handler)

    help_handler = CommandHandler("help", start)
    application.add_handler(help_handler)

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

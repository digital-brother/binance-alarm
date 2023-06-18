import asyncio
import telegram
from django.conf import settings
from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def send_message(chat_id, message):
    bot = telegram.Bot(settings.TELEGRAM_BOT_TOKEN)
    keyboard = [[InlineKeyboardButton("Pause bot for 1 hour", callback_data='alex')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    message = asyncio.run(bot.send_message(chat_id, message, reply_markup=reply_markup))
    return message.id


def update_message(chat_id, message_id, new_message):
    bot = telegram.Bot(settings.TELEGRAM_BOT_TOKEN)
    asyncio.run(bot.edit_message_text(chat_id=chat_id, message_id=message_id, text='new_message'))

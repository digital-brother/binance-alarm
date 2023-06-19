import asyncio
import telegram
from django.conf import settings


def send_message(chat_id, message):
    bot = telegram.Bot(settings.TELEGRAM_BOT_TOKEN)
    message = asyncio.run(bot.send_message(chat_id, message))
    return message.id


def update_message(chat_id, message_id, new_message):
    bot = telegram.Bot(settings.TELEGRAM_BOT_TOKEN)
    asyncio.run(bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=new_message))

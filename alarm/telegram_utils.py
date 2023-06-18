import asyncio
import telegram
from django.conf import settings

bot = telegram.Bot(settings.TELEGRAM_BOT_TOKEN)


def send_message(chat_id, message):
    message = asyncio.run(bot.send_message(chat_id, message))
    return message.id


def update_message(chat_id, message_id, new_message):
    bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=new_message)

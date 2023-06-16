import asyncio
import telegram
from django.conf import settings

bot = telegram.Bot(settings.TELEGRAM_BOT_TOKEN)


def send_message(chat_id, message):
    asyncio.run(bot.send_message(chat_id, message))

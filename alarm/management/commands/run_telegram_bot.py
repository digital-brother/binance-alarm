"""
For an in-depth explanation, check out
https://github.com/python-telegram-bot/python-telegram-bot/wiki/InlineKeyboard-Example.
"""
from django.conf import settings
from django.core.management import BaseCommand
from telegram import Update
from telegram.ext import Application, ContextTypes, CommandHandler

from alarm.models import Phone


async def alarm_message_seen_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await Phone.objects.filter(telegram_chat_id=update.message.chat.id).aupdate(telegram_message_seen=True)


async def get_chat_id_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    context.bot.send_message(chat_id=chat_id, text=f"Your chat ID is {chat_id}")


def run_telegram_bot():
    application = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler("alarm_message_seen", alarm_message_seen_handler))
    application.add_handler(CommandHandler("get_chat_id", get_chat_id_handler))
    application.run_polling(allowed_updates=Update.CALLBACK_QUERY)


class Command(BaseCommand):
    help = 'Gets updates for all trade pairs, analyses if thresholds were broken, ' \
           'makes a call to a user in case of need'

    def handle(self, *args, **options):
        run_telegram_bot()

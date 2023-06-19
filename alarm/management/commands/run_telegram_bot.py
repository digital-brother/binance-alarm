"""
For an in-depth explanation, check out
https://github.com/python-telegram-bot/python-telegram-bot/wiki/InlineKeyboard-Example.
"""
from asgiref.sync import sync_to_async
from django.conf import settings
from django.core.management import BaseCommand
from django.utils import timezone
from telegram import Update
from telegram.ext import Application, ContextTypes, CommandHandler

from alarm.models import Phone


async def alarm_message_seen_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phone = await Phone.objects.filter(number='+380955078262').aupdate(telegram_message_seen=True)


def run_telegram_bot():
    application = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler("alarm_message_seen", alarm_message_seen_handler))
    application.run_polling(allowed_updates=Update.CALLBACK_QUERY)


class Command(BaseCommand):
    help = 'Gets updates for all trade pairs, analyses if thresholds were broken, ' \
           'makes a call to a user in case of need'

    def handle(self, *args, **options):
        run_telegram_bot()

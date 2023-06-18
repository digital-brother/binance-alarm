"""
For an in-depth explanation, check out
https://github.com/python-telegram-bot/python-telegram-bot/wiki/InlineKeyboard-Example.
"""
from django.conf import settings

from django.core.management import BaseCommand
from telegram import Update
from telegram.ext import Application, CallbackQueryHandler, ContextTypes


async def button_pressed_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(text=query.message.text)
    await query.message.reply_text('Bot was paused for 1 hour')


def run_telegram_bot():
    application = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CallbackQueryHandler(button_pressed_handler))
    application.run_polling(allowed_updates=Update.ALL_TYPES)


class Command(BaseCommand):
    help = 'Gets updates for all trade pairs, analyses if thresholds were broken, ' \
           'makes a call to a user in case of need'

    def handle(self, *args, **options):
        run_telegram_bot()

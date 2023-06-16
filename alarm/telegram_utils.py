# import asyncio
# import telegram
#
# bot = telegram.Bot("6182875242:AAHoyBE5VErdAyu_S2XozzcOn2Jo4180EW8")
#
#
# def send_message(chat_id, message):
#     asyncio.run(bot.send_message(chat_id, message))


# import asyncio
#
# import telegram
#
# TELEGRAM_BOT_TOKEN = "6182875242:AAHoyBE5VErdAyu_S2XozzcOn2Jo4180EW8"
# CHAT_ID = '427603106'
# bot = telegram.Bot(TELEGRAM_BOT_TOKEN)
#
#
# async def get_chat_id(update, context):
#     chat_id = update.effective_chat.id
#     await context.bot.send_message(chat_id=chat_id, text=f"Your chat ID is: {chat_id}")
#
#
# def send_telegram_message(chat_id, message):
#     asyncio.run(bot.send_message(chat_id, message))
#
#
# if __name__ == '__main__':
#     send_telegram_message(CHAT_ID, 'Hello, world.')
#     # application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
#     #
#     # start_handler = CommandHandler('get_chat_id', get_chat_id)
#     # application.add_handler(start_handler)
#     #
#     # application.run_polling()

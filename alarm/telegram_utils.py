import asyncio
import telegram

bot = telegram.Bot("6182875242:AAHoyBE5VErdAyu_S2XozzcOn2Jo4180EW8")


def send_message(chat_id, message):
    asyncio.run(bot.send_message(chat_id, message))

def get_message_with_twiml_elements_for_threshold_break(phone, trade_pair):
    message = TradePair(phone, trade_pair).alarm_message()
    message_with_twiml_elements = f"<Response><Say>{message}</Say></Response>"
    return message_with_twiml_elements


def make_call():
    print('MAKE CALL')

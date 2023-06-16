import logging

from django.conf import settings
from twilio.rest import Client

logger = logging.getLogger(f'{__name__}')
client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)


def call(number, message):
    client.calls.create(
        twiml=f'<Response><Say>{message}</Say></Response>',
        to=str(number),
        from_=settings.TWILIO_FROM_PHONE_NUMBER
    )
    logger.info(f"Twilio is calling {number}: '{message}'")

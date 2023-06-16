import logging

from django.conf import settings
from django.core.exceptions import ValidationError
from twilio.rest import Client

logger = logging.getLogger(f'{__name__}')
client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)


def call(number, message):
    call = client.calls.create(
        twiml=f'<Response><Say>{message}</Say></Response>',
        to=str(number),
        from_=settings.TWILIO_FROM_PHONE_NUMBER
    )
    logger.info(f"Twilio is calling {number}: '{message}'")
    return call.sid


def call_succeed(sid):
    if not sid:
        raise ValidationError("No active call found: ringing_twilio_call_sid is not set. ")

    call = client.calls(sid).fetch()

    user_did_not_answer_yet_statuses = ['queued', 'initiated', 'ringing']
    user_skipped_call_statuses = ['no-answer', 'canceled', 'failed']
    user_reacted_statuses = ['in-progress', 'completed', 'busy']

    if call.status in user_did_not_answer_yet_statuses + user_skipped_call_statuses:
        return False
    elif call.status in user_reacted_statuses:
        return True
    else:
        raise ValidationError(f'Unknown status: {call.status}')

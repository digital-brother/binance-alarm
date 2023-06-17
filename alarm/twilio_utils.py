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


def call_status(sid):
    from alarm.models import CallStatus

    if not sid:
        raise ValidationError("No active call found: ringing_twilio_call_sid is not set. ")

    call = client.calls(sid).fetch()
    # Busy means that user saw a call and checked alarm message via Telegram
    call_succeed_statuses = ['in-progress', 'completed', 'busy']
    call_pending_statuses = ['queued', 'initiated', 'ringing']
    call_skipped_statuses = ['no-answer', 'canceled', 'failed']

    if call.status in call_pending_statuses:
        return CallStatus.PENDING
    elif call.status in call_skipped_statuses:
        return CallStatus.SKIPPED
    elif call.status in call_succeed_statuses:
        return CallStatus.SUCCEED
    else:
        raise ValidationError(f'Unknown status: {call.status}')

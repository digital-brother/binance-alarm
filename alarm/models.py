import datetime as dt
import logging
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, AbstractUser
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.db.models import Q
from django.utils import timezone
from phonenumber_field.modelfields import PhoneNumberField

from alarm import telegram_utils, twilio_utils
from alarm.binance_utils import get_binance_valid_trade_pairs
from alarm.exceptions import NoAlarmMessageError, PreviousCallResultsNotFetchedError, NoPreviousCallError, \
    TelegramMessageAlreadyExistsError, NoTelegramMessageError, InactivePhoneHasUnseenThresholdBreaksError, \
    InactivePhoneError

logger = logging.getLogger(f'{__name__}')
User = get_user_model()


class CallStatus(models.TextChoices):
    SUCCEED = 'succeed'
    PENDING = 'pending'
    SKIPPED = 'skipped'


class PhoneManager(models.Manager):
    def active(self, **kwargs):
        return self.filter(
            Q(enabled=True) & Q(
                Q(paused_until__isnull=True) |
                Q(paused_until__lte=timezone.now())),
            **kwargs)


class Phone(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='phones')
    number = PhoneNumberField(unique=True, region='UA')
    telegram_chat_id = models.CharField(max_length=32, unique=True)
    twilio_call_sid = models.CharField(max_length=64, null=True, blank=True)
    telegram_message_id = models.PositiveBigIntegerField(null=True, blank=True)
    current_telegram_message = models.CharField(max_length=1024, null=True, blank=True)
    telegram_message_seen = models.BooleanField(default=False)
    pause_minutes_duration = models.PositiveSmallIntegerField(default=30)
    paused_until = models.DateTimeField(null=True, blank=True)
    enabled = models.BooleanField(default=False)

    objects = PhoneManager()

    def __str__(self):
        return str(self.number)

    @classmethod
    def call_all_suitable_phones(cls):
        for phone in cls.get_needing_call_phones():
            phone.call()

    @classmethod
    def send_or_update_all_telegram_messages(cls):
        phones_to_send_message = cls.get_needing_message_send_phones()
        phones_to_update_message = cls.get_needing_message_update_phones()
        for phone in phones_to_send_message:
            phone.send_telegram_message()
        for phone in phones_to_update_message:
            phone.update_telegram_message()

    @classmethod
    def handle_user_notified_if_calls_succeed(cls):
        for phone in cls.get_needing_call_check_phones():
            phone.handle_user_notified_if_call_succeed()

    @classmethod
    def handle_user_notified_if_messages_seen(cls):
        # In case if telegram message seen button was pressed and phone disabled,
        # we still would like to mark threshold breaks as seen.
        for phone in cls.objects.filter(telegram_message_seen=True):
            phone.mark_threshold_breaks_as_seen()

    def call(self):
        """
        Makes a call and communicates an alarm message from a clean DB state, i.e. as if no any calls were done before.
        Supposed to be used in a combination with handle_user_notified_if_call_succeed.
        """
        if not self.alarm_message:
            raise NoAlarmMessageError('Alarm message should not be empty.')

        if self.twilio_call_sid:
            raise PreviousCallResultsNotFetchedError('Alarm message is not synced with results of a previous call')

        call_sid = twilio_utils.call(self.number, self.alarm_message)
        self.twilio_call_sid = call_sid
        self.save()
        return call_sid

    def handle_user_notified_if_call_succeed(self):
        """
        Syncs alarm message with results of a previous call, as if no any calls were done previously.
        If call succeed - resets alarm messages and removes a previous call info.
        If call was skipped - just removes a previous call info (equals to recall).
        If call is pending - keeps a call as a previous call.

        Discards all thresholds breaks happened after 'Receive call' button was pressed on phone
        till event was caught by Django.
        """

        if not self.twilio_call_sid:
            raise NoPreviousCallError("No twilio_call_sid set. "
                                      "Method should be called only after phone call was done and still not synced")

        call_status = twilio_utils.call_status(self.twilio_call_sid)
        if call_status == CallStatus.SUCCEED:
            logger.info(
                f"User {self.user} was alarmed by phone {self.number} (call_sid={self.twilio_call_sid})")
            # A marking of threshold breaks as seen resets an alarm message
            # as an alarm message is built based on unseen threshold breaks
            self.mark_threshold_breaks_as_seen()
        elif call_status == CallStatus.SKIPPED:
            self.twilio_call_sid = None
            self.save()

    def send_telegram_message(self):
        message = self.alarm_message
        if not message:
            raise NoAlarmMessageError('Message should not be empty.')

        if self.telegram_message_id:
            raise TelegramMessageAlreadyExistsError('Telegram message already exists and is still unseen. '
                                                    'Use update_alarm_telegram_message() method instead.')

        message_id = telegram_utils.send_message(self.telegram_chat_id, message)
        self.telegram_message_id = message_id
        self.current_telegram_message = message
        self.save()
        return message_id

    def update_telegram_message(self):
        message = self.alarm_message
        if not message:
            raise NoAlarmMessageError('Message should not be empty.')

        if not self.telegram_message_id:
            raise NoTelegramMessageError('Telegram message does not exist. Use send_telegram_message() instead.')

        if self.current_telegram_message == message:
            return

        telegram_utils.update_message(self.telegram_chat_id, self.telegram_message_id, message)
        self.current_telegram_message = message
        self.save()

    def mark_threshold_breaks_as_seen(self):
        self.unseen_threshold_breaks.update(seen=True)

        self.telegram_message_id = None
        self.current_telegram_message = None
        self.telegram_message_seen = False

        if self.pause_minutes_duration:
            self.paused_until = timezone.now() + dt.timedelta(minutes=self.pause_minutes_duration)

            paused_until_str = timezone.localtime(self.paused_until).strftime("%Y-%m-%d %H:%M:%S")
            bot_paused_message = f'Bot was paused for {self.pause_minutes_duration} minutes (until {paused_until_str}).'
            telegram_utils.send_message(self.telegram_chat_id, bot_paused_message)

        twilio_utils.cancel_call(self.twilio_call_sid)
        self.twilio_call_sid = None
        self.save()

    @property
    def trade_pairs(self):
        return self.thresholds.distinct().values_list('trade_pair', flat=True)

    @property
    def unseen_threshold_breaks(self):
        # TODO: What if there are unseen threshold breaks for a disabled phone?
        # Should we mark them as seen?
        unseen_threshold_breaks = ThresholdBreak.objects.filter(threshold__phone__number=self.number, seen=False)
        if not self.is_active and unseen_threshold_breaks:
            raise InactivePhoneHasUnseenThresholdBreaksError

        return unseen_threshold_breaks

    @property
    def alarm_message(self):
        trade_pairs_alarm_messages = []

        for trade_pair in self.trade_pairs:
            trade_pair_unseen_threshold_breaks = TradePair(self, trade_pair).unseen_threshold_breaks
            if trade_pair_unseen_threshold_breaks:
                trade_pair_alarm_message = TradePair(self, trade_pair).alarm_message
                trade_pairs_alarm_messages.append(trade_pair_alarm_message)

        if not trade_pairs_alarm_messages:
            return None

        alarm_message = '\n'.join(trade_pairs_alarm_messages)
        return alarm_message

    @property
    def is_active(self):
        return self in Phone.objects.active()

    @classmethod
    def get_needing_call_phones(cls):
        return [phone for phone in cls.objects.active().filter(twilio_call_sid__isnull=True)
                if phone.unseen_threshold_breaks]

    @classmethod
    def get_needing_call_check_phones(cls):
        return [phone for phone in cls.objects.active().filter(twilio_call_sid__isnull=False)
                if phone.unseen_threshold_breaks]

    @classmethod
    def get_needing_message_send_phones(cls):
        return [phone for phone in cls.objects.active().filter(telegram_message_id__isnull=True)
                if phone.unseen_threshold_breaks]

    @classmethod
    def get_needing_message_update_phones(cls):
        return [phone for phone in Phone.objects.active().filter(telegram_message_id__isnull=False)
                if phone.unseen_threshold_breaks]


class TradePair:
    def __init__(self, phone, trade_pair):
        self.phone = phone
        self.trade_pair = trade_pair

    @property
    def unseen_threshold_breaks(self):
        # TODO: What if there is an unseen threshold break for a disabled phone?
        # Should we mark them as seen?
        return ThresholdBreak.objects.filter(
            threshold__phone=self.phone, threshold__trade_pair=self.trade_pair, seen=False)

    @property
    def thresholds(self):
        return Threshold.objects.filter(phone=self.phone, trade_pair=self.trade_pair)

    @property
    def display_name(self):
        return self.get_display_name(self.trade_pair)

    @staticmethod
    def get_display_name(trade_pair):
        display_name = trade_pair.replace('USDT', '').upper()
        return display_name

    @property
    def close_price(self):
        last_candle = Candle.last_for_trade_pair(self.trade_pair)
        return last_candle.close_price if last_candle else None

    @property
    def thresholds_breaks_prices_str(self):
        unseen_threshold_break_prices = \
            self.unseen_threshold_breaks.order_by('happened_at').values_list('threshold__price', flat=True)
        thresholds_break_prices_str = ', '.join([f'{price}' for price in unseen_threshold_break_prices])
        return thresholds_break_prices_str

    @property
    def alarm_message(self):
        if not self.thresholds_breaks_prices_str:
            return None

        message = f"{self.display_name} broken thresholds {self.thresholds_breaks_prices_str} " \
                  f"and the current {self.display_name} price is {self.close_price}."
        return message

    @classmethod
    def create_thresholds_breaks_from_recent_candles_update(cls, trade_pair):
        # We do not create threshold breaks in case if phone is inactive
        thresholds = Threshold.objects.active().filter(trade_pair=trade_pair)
        last_candle = Candle.last_for_trade_pair(trade_pair=trade_pair)
        penultimate_candle = Candle.penultimate_for_trade_pair(trade_pair=trade_pair)

        if last_candle is None:
            return []

        threshold_breaks = []
        for threshold in thresholds:
            threshold_broken = threshold.is_broken(penultimate_candle, last_candle)
            logger.info(f"{str(trade_pair).upper()}; "
                        f"candles: {penultimate_candle}, {last_candle}, {threshold.trade_pair_obj.close_price}; "
                        f"threshold: {threshold}; "
                        f"threshold broken: {threshold_broken};")
            if threshold_broken:
                threshold_break = threshold.create_threshold_break_if_needed()
                threshold_breaks.append(threshold_break)

        return threshold_breaks


class ThresholdManager(models.Manager):
    def active(self, **kwargs):
        return self.filter(phone__in=Phone.objects.active(), **kwargs)


class Threshold(models.Model):
    phone = models.ForeignKey(Phone, on_delete=models.CASCADE, related_name='thresholds')
    trade_pair = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=4)

    objects = ThresholdManager()

    class Meta:
        unique_together = ['phone', 'trade_pair', 'price']

    def __str__(self):
        trade_pair_display_name = TradePair.get_display_name(self.trade_pair)
        return f"{trade_pair_display_name}: {self.price}"

    def clean(self):
        super().clean()

        # Optimized for performance to avoid requesting Binance API while getting a trade pair display name
        if not self.trade_pair.endswith('USDT'):
            raise ValidationError("Trade pair name should end with 'USDT'. For example, ETHUSDT.")

        valid_trade_pairs = get_binance_valid_trade_pairs().keys()
        if self.trade_pair not in valid_trade_pairs:
            raise ValidationError(
                f"{self.trade_pair} is not a valid coin abbreviation. For example, ETHUSDT.")

    @property
    def trade_pair_obj(self):
        return TradePair(self.phone, self.trade_pair)

    def is_broken(self, previous_candle, current_candle):
        # TODO: handle a case when program was paused for a while and price changed a lot
        if previous_candle and current_candle:
            return (
                    min(previous_candle.low_price, current_candle.low_price) <=
                    self.price <=
                    max(previous_candle.high_price, current_candle.high_price)
            )
        elif current_candle:
            return current_candle.low_price <= self.price <= current_candle.high_price

        return False

    def create_threshold_break_if_needed(self):
        if not self.phone.is_active:
            raise InactivePhoneError("Threshold break cannot be generated for an inactive phone. "
                                     "Check that phone is enabled and not paused.")

        last_unseen_trade_pair_threshold_break = TradePair(self.phone, self.trade_pair).unseen_threshold_breaks.last()
        is_duplicate_threshold_break = self == last_unseen_trade_pair_threshold_break.threshold \
            if last_unseen_trade_pair_threshold_break else None
        if is_duplicate_threshold_break:
            return last_unseen_trade_pair_threshold_break, False
        ThresholdBreak.objects.create(threshold=self)


class Candle(models.Model):
    trade_pair = models.CharField(max_length=255)
    modified = models.DateTimeField(auto_now=True)
    low_price = models.DecimalField(max_digits=10, decimal_places=2)
    high_price = models.DecimalField(max_digits=10, decimal_places=2)
    close_price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        trade_pair_display_name = TradePair.get_display_name(self.trade_pair)
        return f"{trade_pair_display_name}: {self.low_price} - {self.high_price}"

    @classmethod
    def last_for_trade_pair(cls, trade_pair):
        return cls.objects.filter(trade_pair=trade_pair).order_by('modified').last()

    @classmethod
    def penultimate_for_trade_pair(cls, trade_pair):
        # Negative indexing for Django querysets is not supported
        trade_pair_candles = cls.objects.filter(trade_pair=trade_pair).order_by('-modified')
        if trade_pair_candles.count() < 2:
            return None
        return trade_pair_candles[1]

    @classmethod
    @transaction.atomic
    def refresh_candle_data(cls, trade_pair, high_price, low_price, close_price):
        """Also deletes old candles, which we do not need anymore"""
        candle_to_keep = cls.objects.filter(trade_pair=trade_pair).order_by('modified').last()

        if candle_to_keep:
            cls.objects.filter(trade_pair=trade_pair).exclude(pk=candle_to_keep.pk).delete()

        candle = cls.objects.create(trade_pair=trade_pair, high_price=high_price, low_price=low_price,
                                    close_price=close_price)
        return candle


class ThresholdBreak(models.Model):
    threshold = models.ForeignKey(Threshold, on_delete=models.CASCADE, related_name='threshold_breaks')
    happened_at = models.DateTimeField(auto_now_add=True)
    seen = models.BooleanField(default=False)

    def __str__(self):
        happened_at_str = self.happened_at.strftime('%Y-%m-%d %H:%M')
        trade_pair_display_name = TradePair.get_display_name(self.threshold.trade_pair)
        return f"{trade_pair_display_name}: {self.threshold.price} ({happened_at_str})"

import logging

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, AbstractUser, User
from django.core.exceptions import ValidationError
from django.db import models, transaction
from phonenumber_field.modelfields import PhoneNumberField

from alarm.binance_utils import get_binance_valid_trade_pairs

logger = logging.getLogger(f'{__name__}')


class Phone(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    number = PhoneNumberField(blank=True, unique=True, region='UA')
    enabled = models.BooleanField(default=False)
    message = models.TextField(null=True, blank=True)

    def __str__(self):
        return str(self.number)

    @property
    def trade_pairs(self):
        return self.thresholds.distinct().values_list('trade_pair', flat=True)

    @property
    def threshold_brakes(self):
        return ThresholdBrake.objects.filter(threshold__phone__number=self.number)

    def get_trade_pair_threshold_brakes(self, trade_pair):
        return self.threshold_brakes.filter(threshold__trade_pair=trade_pair)

    def refresh_alarm_message(self):
        from alarm.utils import get_trade_pair_alarm_message

        trade_pairs_alarm_messages = []
        for trade_pair in self.trade_pairs:
            trade_pair_broken_thresholds = self.get_trade_pair_threshold_brakes(trade_pair)
            if trade_pair_broken_thresholds:
                trade_pair_alarm_message = get_trade_pair_alarm_message(self.number, trade_pair)
                trade_pairs_alarm_messages.append(trade_pair_alarm_message)

        self.message = ' '.join(trade_pairs_alarm_messages)
        self.save()

    # TODO: Remove an unused method
    @classmethod
    def refresh_alarm_messages_for_all_phones(cls):
        phones = cls.objects.all()
        for phone in phones:
            phone.refresh_alarm_message()


class TradePair:
    def __init__(self, phone, trade_pair):
        self.phone = phone
        self.trade_pair = trade_pair

    @property
    def threshold_brakes(self):
        return ThresholdBrake.objects.filter(threshold__phone=self.phone, trade_pair=self.trade_pair)

    @property
    def thresholds(self):
        return Threshold.objects.filter(phone=self.phone, trade_pair=self.trade_pair)

    @property
    def display_value(self):
        """
        Gets Binance trade pair info by trade pair name,
        returns 'base_asset/quote_asset' trade pair string representation
        """
        binance_valid_trade_pairs = get_binance_valid_trade_pairs()
        trade_pair_info = binance_valid_trade_pairs.get(self.trade_pair)
        if trade_pair_info is None:
            raise ValueError(f"{self.trade_pair} is not a valid Binance trade pair.")

        base_asset = trade_pair_info['baseAsset']
        quote_asset = trade_pair_info['quoteAsset']
        return f"{base_asset}/{quote_asset}"

    @property
    def close_price(self):
        last_candle = Candle.last_for_trade_pair(self.trade_pair)
        return last_candle.close_price if last_candle else None

    @property
    def thresholds_brakes_prices_str(self):
        threshold_brake_prices = \
            self.threshold_brakes.order_by('-happened_at').values_list('threshold__price', flat=True)
        thresholds_brake_prices_str = ', '.join([f'{price}$' for price in threshold_brake_prices])
        return thresholds_brake_prices_str

    def get_trade_pair_alarm_message(self):
        message = f"{self.trade_pair} broken thresholds {self.thresholds_brakes_prices_str} " \
                  f"and the current {self.trade_pair} price is {self.close_price}$."

        return message

    @classmethod
    def create_thresholds_brakes_from_recent_candles_update(cls, trade_pair):
        thresholds = Threshold.objects.filter(trade_pair=trade_pair)
        last_candle = Candle.last_for_trade_pair(trade_pair=trade_pair)
        penultimate_candle = Candle.penultimate_for_trade_pair(trade_pair=trade_pair)

        if last_candle is None or penultimate_candle is None:
            return []

        threshold_brakes = []
        for threshold in thresholds:
            threshold_broken = threshold.is_broken(last_candle, penultimate_candle)
            logger.info(f"{str(trade_pair).upper()}; "
                        f"candles: {penultimate_candle}, {last_candle}, {threshold.trade_pair_obj.close_price}; "
                        f"threshold: {threshold}; "
                        f"threshold broken: {threshold_broken};")
            if threshold_broken:
                threshold_brake = threshold.create_threshold_brake_if_needed()
                threshold_brakes.append(threshold_brake)

        return threshold_brakes


class Threshold(models.Model):
    phone = models.ForeignKey(Phone, on_delete=models.CASCADE, related_name='thresholds')
    trade_pair = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        unique_together = ['phone', 'trade_pair', 'price']

    def __str__(self):
        return f"{self.price}"

    def clean(self):
        super().clean()

        valid_trade_pairs = get_binance_valid_trade_pairs().keys()
        if self.trade_pair not in valid_trade_pairs:
            raise ValidationError(
                f"{self.trade_pair} is not a valid coin abbreviation. For example, ethusdt or ethbtc.")

    @property
    def trade_pair_obj(self):
        return TradePair(self.phone, self.trade_pair)

    def is_broken(self, previous_candle, current_candle):
        # TODO: handle a case when program was paused for a while and price changed a lot
        # TODO: handle case when penultimate candle is absent
        if previous_candle and current_candle:
            return (
                    min(previous_candle.low_price, current_candle.low_price) <=
                    self.price <=
                    max(previous_candle.high_price, current_candle.high_price)
            )
        return False

    def create_threshold_brake_if_needed(self):
        last_trade_pair_threshold_brake = TradePair(self.phone, self.trade_pair).threshold_brakes.last()
        is_duplicate_threshold_brake = self == last_trade_pair_threshold_brake.threshold
        if is_duplicate_threshold_brake:
            return last_trade_pair_threshold_brake, False
        ThresholdBrake.objects.create(threshold=self)


class Candle(models.Model):
    # TODO: Possibly extract trade_pair model
    trade_pair = models.CharField(max_length=255)
    modified = models.DateTimeField(auto_now=True)
    high_price = models.DecimalField(max_digits=10, decimal_places=2)
    low_price = models.DecimalField(max_digits=10, decimal_places=2)
    close_price = models.DecimalField(max_digits=10, decimal_places=2)

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

    def __str__(self):
        return f"{self.trade_pair}: {self.low_price}$ - {self.high_price}$"


class ThresholdBrake(models.Model):
    threshold = models.ForeignKey(Threshold, on_delete=models.CASCADE, related_name='threshold_brakes')
    happened_at = models.DateTimeField(auto_now_add=True)
    user_notified = models.BooleanField(default=False)

    def __str__(self):
        happened_at_str = self.happened_at.strftime('%Y-%m-%d %H:%M')
        return f"{self.threshold.trade_pair} - {self.threshold.price} - {happened_at_str}"

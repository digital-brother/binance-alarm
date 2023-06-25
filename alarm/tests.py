import datetime as dt
from django.utils import timezone
from unittest.mock import patch, Mock

import decimal

import pytest
from decimal import Decimal
from django.core.exceptions import ValidationError
from pytest_factoryboy import register

from alarm.exceptions import NoAlarmMessageError, TelegramMessageAlreadyExistsError, NoPreviousCallError, \
    PreviousCallResultsNotFetchedError, NoTelegramMessageError
from alarm.factories import ThresholdFactory, CandleFactory, ThresholdBreakFactory, PhoneFactory, UserFactory
from alarm.models import TradePair, ThresholdBreak, CallStatus

pytestmark = pytest.mark.django_db

register(UserFactory)
register(PhoneFactory)
register(ThresholdFactory)
register(ThresholdBreakFactory)
register(CandleFactory)


class TestThresholdIsBroken:
    def test__threshold_is_broken__single_candle(self):
        threshold = ThresholdFactory(price=Decimal('10.00'))
        candle = CandleFactory(low_price=Decimal('9.00'), high_price=Decimal('11.00'))
        assert threshold.is_broken(None, candle)

    def test__threshold_not_broken__single_candle(self):
        threshold = ThresholdFactory(price=Decimal('10.00'))
        candle = CandleFactory(low_price=Decimal('8.00'), high_price=Decimal('9.00'))
        assert not threshold.is_broken(None, candle)

    def test__threshold_is_broken__two_candles(self):
        threshold = ThresholdFactory(price=Decimal('10.00'))
        first_candle = CandleFactory(low_price=Decimal('7.00'), high_price=Decimal('9.00'))
        second_candle = CandleFactory(low_price=Decimal('8.00'), high_price=Decimal('11.00'))
        assert threshold.is_broken(first_candle, second_candle)

    def test__threshold_not_broken__two_candles(self):
        threshold = ThresholdFactory(price=Decimal('10.00'))
        first_candle = CandleFactory(low_price=Decimal('7.00'), high_price=Decimal('8.00'))
        second_candle = CandleFactory(low_price=Decimal('8.00'), high_price=Decimal('9.00'))
        assert not threshold.is_broken(first_candle, second_candle)

    def test__threshold_is_broken__two_candles_with_gap(self):
        threshold = ThresholdFactory(price=Decimal('10.00'))
        first_candle = CandleFactory(low_price=Decimal('7.00'), high_price=Decimal('8.00'))
        second_candle = CandleFactory(low_price=Decimal('12.00'), high_price=Decimal('13.00'))
        assert threshold.is_broken(first_candle, second_candle)


class TestCreateThresholdBreak:
    def test__create_threshold_break__threshold_broken(self):
        trade_pair = 'LUNAUSDT'
        threshold = ThresholdFactory(price=Decimal('10.00'), trade_pair=trade_pair)
        CandleFactory(low_price=Decimal('9.00'), high_price=Decimal('11.00'), trade_pair=trade_pair)
        TradePair.create_thresholds_breaks_from_recent_candles_update(trade_pair)
        assert ThresholdBreak.objects.count() == 1
        assert ThresholdBreak.objects.first().threshold == threshold

    def test__create_threshold_break__does_not_create_duplicate(self):
        trade_pair = 'LUNAUSDT'
        threshold = ThresholdFactory(price=Decimal('10.00'), trade_pair=trade_pair)
        CandleFactory(low_price=Decimal('9.00'), high_price=Decimal('11.00'), trade_pair=trade_pair)
        TradePair.create_thresholds_breaks_from_recent_candles_update(trade_pair)
        TradePair.create_thresholds_breaks_from_recent_candles_update(trade_pair)
        assert ThresholdBreak.objects.count() == 1

    @pytest.mark.xfail
    def test__create_threshold_break__does_not_create_duplicate_for_two_thresholds(self, threshold):
        trade_pair = 'LUNAUSDT'
        ThresholdFactory(price=Decimal('12.00'), trade_pair=threshold.trade_pair, phone=threshold.phone)
        CandleFactory(low_price=Decimal('8.00'), high_price=Decimal('14.00'), trade_pair=trade_pair)
        TradePair.create_thresholds_breaks_from_recent_candles_update(trade_pair)
        TradePair.create_thresholds_breaks_from_recent_candles_update(trade_pair)
        assert ThresholdBreak.objects.count() == 2

    def test__create_threshold_break__threshold_not_broken(self):
        trade_pair = 'LUNAUSDT'
        ThresholdFactory(price=Decimal('10.00'), trade_pair=trade_pair)
        CandleFactory(low_price=Decimal('8.00'), high_price=Decimal('9.00'), trade_pair=trade_pair)
        TradePair.create_thresholds_breaks_from_recent_candles_update(trade_pair)
        assert ThresholdBreak.objects.count() == 0

    def test__create_threshold_break__phone_disabled(self):
        trade_pair = 'LUNAUSDT'
        phone = PhoneFactory(enabled=False)
        threshold = ThresholdFactory(price=Decimal('10.00'), trade_pair=trade_pair, phone=phone)
        CandleFactory(low_price=Decimal('9.00'), high_price=Decimal('11.00'), trade_pair=trade_pair)
        TradePair.create_thresholds_breaks_from_recent_candles_update(trade_pair)
        assert ThresholdBreak.objects.count() == 0

    @patch('alarm.models.telegram_utils.send_message', Mock(return_value=5))
    @patch('alarm.models.twilio_utils.cancel_call', Mock(return_value=5))
    def test__create_threshold_break__phone_paused(self):
        """Checks, that after a user was notified, threshold breaks are not created """
        trade_pair = 'LUNAUSDT'
        threshold = ThresholdFactory(price=Decimal('10.00'), trade_pair=trade_pair)
        CandleFactory(low_price=Decimal('9.00'), high_price=Decimal('11.00'), trade_pair=trade_pair)
        TradePair.create_thresholds_breaks_from_recent_candles_update(trade_pair)
        assert threshold.phone.unseen_threshold_breaks.count() == 1
        threshold.phone.mark_threshold_breaks_as_seen()

        CandleFactory(low_price=Decimal('9.00'), high_price=Decimal('11.00'), trade_pair=trade_pair)
        TradePair.create_thresholds_breaks_from_recent_candles_update(trade_pair)
        assert threshold.phone.unseen_threshold_breaks.count() == 0


class TestTradePairAlarmMessage:
    def test__trade_pair_alarm_message__no_threshold_breaks(self, phone):
        trade_pair_obj = TradePair(phone=phone, trade_pair='LUNAUSDT')
        assert trade_pair_obj.alarm_message is None

    def test__trade_pair_alarm_message__single_threshold_break(self):
        threshold_break = ThresholdBreakFactory()
        CandleFactory()
        trade_pair_obj = TradePair(phone=threshold_break.threshold.phone, trade_pair=threshold_break.threshold.trade_pair)
        assert trade_pair_obj.alarm_message == \
               'LUNA broken thresholds 10.00 and the current LUNA price is 14.00.'

    def test__trade_pair_alarm_message__another_trade_pair_threshold_break_not_shown(self, threshold_break):
        wing_threshold = ThresholdFactory(trade_pair='wingusdt', phone=threshold_break.threshold.phone)
        ThresholdBreakFactory(threshold=wing_threshold)
        CandleFactory()
        trade_pair_obj = TradePair(phone=threshold_break.threshold.phone, trade_pair=threshold_break.threshold.trade_pair)
        assert trade_pair_obj.alarm_message == \
               'LUNA broken thresholds 10.00 and the current LUNA price is 14.00.'

    def test__trade_pair_alarm_message__three_threshold_breaks(self):
        first_threshold = ThresholdFactory()
        second_threshold = ThresholdFactory(phone=first_threshold.phone, price=decimal.Decimal('12.00'))

        first_threshold_break = ThresholdBreakFactory(threshold=first_threshold)
        ThresholdBreakFactory(threshold=second_threshold)
        ThresholdBreakFactory(threshold=first_threshold)

        CandleFactory()

        trade_pair_obj = TradePair(
            phone=first_threshold_break.threshold.phone, trade_pair=first_threshold_break.threshold.trade_pair)
        assert trade_pair_obj.alarm_message == \
               'LUNA broken thresholds 10.00, 12.00, 10.00 and the current LUNA price is 14.00.'


class TestPhoneAlarmMessage:
    def test__phone_alarm_message__no_breaks(self, phone):
        assert phone.alarm_message is None

    def test__phone_alarm_message__single_trade_pair_broken(self, threshold_break, candle):
        assert threshold_break.threshold.phone.alarm_message == \
               'LUNA broken thresholds 10.00 and the current LUNA price is 14.00.'

    def test__phone_alarm_message__two_trade_pairs_broken(self, threshold_break, candle):
        threshold_two = ThresholdFactory(trade_pair='WINGUSDT', price='20.00', phone=threshold_break.threshold.phone)
        CandleFactory(trade_pair='WINGUSDT', close_price=decimal.Decimal('24.00'))
        ThresholdBreakFactory(threshold=threshold_two)
        assert threshold_break.threshold.phone.alarm_message == \
               'LUNA broken thresholds 10.00 and the current LUNA price is 14.00.\n' \
               'WING broken thresholds 20.00 and the current WING price is 24.00.'

    def test__phone_alarm_message__another_phone_trade_pair_broken(self, threshold_break, candle):
        ThresholdBreakFactory()
        assert threshold_break.threshold.phone.alarm_message == \
               'LUNA broken thresholds 10.00 and the current LUNA price is 14.00.'


def test__create_threshold_breaks_and_get_alarm_message():
    second_trade_pair = 'WINGUSDT'
    threshold = ThresholdFactory(price=decimal.Decimal(10.00))
    # Second trade pair threshold
    ThresholdFactory(price=decimal.Decimal(12.00), trade_pair=threshold.trade_pair, phone=threshold.phone)
    # Second trade pair threshold
    ThresholdFactory(trade_pair=second_trade_pair, price=decimal.Decimal(25.00), phone=threshold.phone)
    # Another phone threshold
    ThresholdFactory(price=decimal.Decimal(14.00), trade_pair=threshold.trade_pair)

    CandleFactory(low_price=decimal.Decimal(8.00), high_price=decimal.Decimal(16.00))
    CandleFactory(trade_pair=second_trade_pair, low_price=decimal.Decimal(21.00), high_price=decimal.Decimal(29.00))
    TradePair.create_thresholds_breaks_from_recent_candles_update(threshold.trade_pair)
    TradePair.create_thresholds_breaks_from_recent_candles_update(second_trade_pair)
    assert ThresholdBreak.objects.count() == 4
    assert threshold.phone.alarm_message == \
           'LUNA broken thresholds 10.00, 12.00 and the current LUNA price is 12.00.\n' \
           'WING broken thresholds 25.00 and the current WING price is 25.00.'


class TestPhoneCall:
    @pytest.mark.raises(exception=NoAlarmMessageError)
    def test__call__no_alarm_message(self, phone):
        phone.call()

    @pytest.mark.raises(exception=PreviousCallResultsNotFetchedError)
    @patch('alarm.models.twilio_utils.call', Mock(return_value='twilio_sid'))
    def test__call__alarm_message_not_synced(self, threshold_break):
        phone = threshold_break.threshold.phone
        phone.call()
        phone.call()

    @pytest.mark.raises(exception=NoPreviousCallError)
    def test__handle_user_notified_if_call_succeed__no_previous_call(self, phone):
        phone.handle_user_notified_if_call_succeed()

    @patch('alarm.models.twilio_utils.call', Mock(return_value='twilio_sid'))
    @patch('alarm.models.twilio_utils.call_status', Mock(return_value=CallStatus.SUCCEED))
    @patch('alarm.models.telegram_utils.send_message', Mock())
    @patch('alarm.models.twilio_utils.cancel_call', Mock())
    def test__handle_user_notified_if_call_succeed__after_user_notified(self, threshold_break):
        phone = threshold_break.threshold.phone
        phone.call()
        phone.handle_user_notified_if_call_succeed()
        assert phone.alarm_message is None


class TestSendUpdateMessage:
    @pytest.mark.raises(exception=NoAlarmMessageError)
    def test__send_message__no_alarm_message(self, phone):
        phone.send_telegram_message()

    @pytest.mark.raises(exception=TelegramMessageAlreadyExistsError)
    def test__send__message__message_already_exists(self, threshold_break):
        phone = threshold_break.threshold.phone
        phone.telegram_message_id = 5
        phone.save()
        phone.send_telegram_message()

    @patch('alarm.models.telegram_utils.send_message', Mock(return_value=5))
    def test__send_message__telegram_message_id_set(self, threshold_break):
        phone = threshold_break.threshold.phone
        assert not phone.telegram_message_id
        phone.send_telegram_message()
        assert phone.telegram_message_id == 5

    @patch('alarm.models.telegram_utils.send_message', Mock(return_value=5))
    def test__send_message__telegram_message_set(self, threshold_break):
        phone = threshold_break.threshold.phone
        message = phone.alarm_message
        assert not phone.current_telegram_message
        phone.send_telegram_message()
        assert phone.current_telegram_message == message

    @pytest.mark.raises(exception=NoAlarmMessageError)
    def test__update_message__no_alarm_message(self, phone):
        phone.send_telegram_message()

    @pytest.mark.raises(exception=NoTelegramMessageError)
    def test__update__message__message_does_not_exist(self, threshold_break):
        threshold_break.threshold.phone.update_telegram_message()

    @patch('alarm.models.telegram_utils.update_message', Mock(return_value=5))
    def test__update__message__message_updated(self, threshold_break):
        phone = threshold_break.threshold.phone
        phone.current_telegram_message = 'Test_message'
        phone.telegram_message_id = 5

        message = phone.alarm_message
        phone.update_telegram_message()
        assert phone.current_telegram_message == message


class TestMarkThresholdBreaksAsSeen:
    @patch('alarm.models.telegram_utils.send_message', Mock(return_value=5))
    @patch('alarm.models.twilio_utils.cancel_call', Mock(return_value=5))
    def test__mark_threshold_breaks_as_seen__telegram_message_reset(self):
        phone = PhoneFactory(current_telegram_message='test_message', telegram_message_id=5)
        phone.mark_threshold_breaks_as_seen()
        assert not phone.alarm_message
        assert not phone.telegram_message_id

    @patch('alarm.models.telegram_utils.send_message', Mock(return_value=5))
    @patch('alarm.models.twilio_utils.cancel_call', Mock(return_value=5))
    def test__mark_threshold_breaks_as_seen__twilio_call_cancelled(self):
        phone = PhoneFactory(current_telegram_message='test_message', telegram_message_id=5)
        phone.mark_threshold_breaks_as_seen()
        assert not phone.alarm_message
        assert not phone.telegram_message_id


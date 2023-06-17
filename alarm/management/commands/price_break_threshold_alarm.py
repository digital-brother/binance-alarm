import logging

from django.core.management.base import BaseCommand

from alarm.binance_utils import connect_binance_socket, \
    parse_candle_from_websocket_update
from alarm.models import Threshold, Candle, TradePair, Phone

logger = logging.getLogger(f'{__name__}')


class Command(BaseCommand):
    help = 'Gets updates for all trade pairs, analyses if thresholds were broken, ' \
           'makes a call to a user in case of need'

    def handle(self, *args, **options):
        trade_pairs = [threshold.trade_pair for threshold in Threshold.objects.all()]
        socket = connect_binance_socket(trade_pairs)

        try:
            while True:
                # TODO: update to include phones whose thresholds were marked as seen
                affected_phones = {}

                binance_data = socket.recv()
                # Placed here to be triggered first after pause caused by socket.recv()
                Phone.sync_all_suitable_phones_alarm_messages()

                high_price, low_price, close_price, trade_pair = parse_candle_from_websocket_update(binance_data)
                Candle.refresh_candle_data(trade_pair, high_price, low_price, close_price)

                created_threshold_brakes = TradePair.create_thresholds_brakes_from_recent_candles_update(trade_pair)

                # Telegram logic
                affected_phones = affected_phones.union(
                    {threshold_brake.threshold.phone for threshold_brake in created_threshold_brakes})
                for phone in affected_phones:
                    phone.send_alarm_telegram_message()

                # Phone logic
                # Placed here to be triggered after alarm message is updated due to
                # a previous call status sync and new candles data
                Phone.call_or_recall_all_suitable_phones()

                # TODO: recheck logic
                # Check if new trade pair appear in the database
                new_trade_pairs = [threshold.trade_pair for threshold in Threshold.objects.all()
                                   if threshold.trade_pair not in trade_pairs]
                if new_trade_pairs:
                    logger.info(f"New trade pairs added: {new_trade_pairs}")
                    trade_pairs += new_trade_pairs
                    new_socket = connect_binance_socket(trade_pairs)
                    socket = new_socket

        except KeyboardInterrupt:
            socket.close()
        except (ValueError, KeyError) as err:
            logger.error(err)

        socket.close()

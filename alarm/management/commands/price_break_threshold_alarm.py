import logging

from django.core.management.base import BaseCommand

from alarm.binance_utils import connect_binance_socket, close_binance_socket, \
    parse_candle_from_websocket_update
from alarm.models import Threshold, Candle
from alarm.utils import make_call, refresh_message_about_threshold_break, \
    create_thresholds_brakes_from_recent_candles_update

logger = logging.getLogger(f'{__name__}')


class Command(BaseCommand):
    help = 'Gets updates for all trade pairs, analyses if thresholds were broken, ' \
           'makes a call to a user in case of need'

    def handle(self, *args, **options):
        trade_pairs = [threshold.trade_pair for threshold in Threshold.objects.all()]
        socket = connect_binance_socket(trade_pairs)

        try:
            while True:
                binance_data = socket.recv()

                high_price, low_price, trade_pair = parse_candle_from_websocket_update(binance_data)

                Candle.refresh_candle_data(trade_pair, high_price, low_price)

                if create_thresholds_brakes_from_recent_candles_update(trade_pair):
                    refresh_message_about_threshold_break()
                    make_call()

                # Check if new trade pair appear in the database
                new_trade_pairs = [threshold.trade_pair for threshold in Threshold.objects.all()
                                   if threshold.trade_pair not in trade_pairs]
                if new_trade_pairs:
                    logger.info(f"New trade pairs added: {new_trade_pairs}")
                    trade_pairs += new_trade_pairs
                    new_socket = connect_binance_socket(trade_pairs)
                    socket = new_socket

        except KeyboardInterrupt:
            close_binance_socket(socket)
        except (ValueError, KeyError) as err:
            logger.error(err)

        close_binance_socket(socket)

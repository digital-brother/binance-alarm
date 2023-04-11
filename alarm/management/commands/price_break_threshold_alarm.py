import logging

from django.core.management.base import BaseCommand

from alarm.binance_utils import connect_binance_sockets, close_binance_sockets, \
    parse_candle_from_websocket_update
from alarm.models import Threshold, Candle
from alarm.utils import any_of_key_pair_thresholds_is_broken

logger = logging.getLogger(f'django.{__name__}')


class Command(BaseCommand):
    help = 'Starts streaming Binance market data'

    def handle(self, *args, **options):
        # Define the list of currencies and intervals you want to stream
        trade_pairs = [threshold.trade_pair for threshold in Threshold.objects.all()]

        # Connect to Binance exchange
        sockets = connect_binance_sockets(trade_pairs)

        # Start processing messages
        try:
            while True:
                for socket in sockets:
                    binance_data = socket.recv()

                    high_price, low_price, trade_pair = parse_candle_from_websocket_update(binance_data)
                    Candle.save_as_recent(trade_pair, high_price, low_price)

                    if any_of_key_pair_thresholds_is_broken(trade_pair):
                        # TODO: make_call()
                        logger.info('need call')
                        pass

                    # Check if new coin names appear in the database
                    new_trade_pairs = [threshold.trade_pair for threshold in Threshold.objects.all()
                                       if threshold.trade_pair not in trade_pairs]
                    if new_trade_pairs:
                        logger.info(f"New trade pairs added: {', '.join(new_trade_pairs)}")
                        trade_pairs += new_trade_pairs
                        new_sockets = connect_binance_sockets(new_trade_pairs)
                        sockets.extend(new_sockets)

        except KeyboardInterrupt:
            close_binance_sockets(sockets)
        except (ValueError, KeyError) as err:
            logger.error(err)

        # Close sockets when finished
        close_binance_sockets(sockets)

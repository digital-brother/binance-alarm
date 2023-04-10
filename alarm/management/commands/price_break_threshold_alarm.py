from django.core.management.base import BaseCommand

from alarm.binance_utils import connect_binance_sockets, close_binance_sockets, \
    parse_kindle_data, print_binance_candle_data
from alarm.models import Threshold, Candle
from alarm.utils import any_of_key_pair_thresholds_is_broken


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

                    current_candle_high_price, current_candle_low_price, trade_pair = \
                        parse_kindle_data(binance_data)

                    current_candle = Candle.update_or_create(trade_pair, current_candle_high_price,
                                                             current_candle_low_price)

                    if any_of_key_pair_thresholds_is_broken(trade_pair, current_candle):
                        # TODO: make_call()
                        print('need call')
                        pass

                    # Check if new coin names appear in the database
                    new_trade_pairs = [threshold.trade_pair for threshold in Threshold.objects.all()
                                       if threshold.trade_pair not in trade_pairs]
                    if new_trade_pairs:
                        print(f"New trade pairs added: {', '.join(new_trade_pairs)}")
                        trade_pairs += new_trade_pairs
                        new_sockets = connect_binance_sockets(new_trade_pairs)
                        sockets.extend(new_sockets)

        except KeyboardInterrupt:
            close_binance_sockets(sockets)
        except (ValueError, KeyError) as err:
            print(err)

        # Close sockets when finished
        close_binance_sockets(sockets)

from django.core.management.base import BaseCommand
from django.db import transaction

from alarm.models import Threshold
from alarm.binance_utils import connect_binance_sockets, close_binance_sockets
from alarm.utils import threshold_is_broken, update_coin_candle_from_binance_data


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

                    coin_prices_data = update_coin_candle_from_binance_data(
                        binance_data)

                    if threshold_is_broken(coin_prices_data):
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

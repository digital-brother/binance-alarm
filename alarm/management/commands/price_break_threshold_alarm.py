from django.core.management.base import BaseCommand
from django.db import transaction

from alarm.models import Coin
from alarm.binance_utils import connect_binance_socket, close_binance_sockets
from alarm.utils import is_threshold_breaks, update_coin_candle_from_binance_data


class Command(BaseCommand):
    help = 'Starts streaming Binance market data'

    def handle(self, *args, **options):
        # Define the list of currencies and intervals you want to stream
        currencies = [coin.abbreviation for coin in Coin.objects.all()]

        # Connect to Binance exchange
        sockets = connect_binance_socket(currencies)

        # Start processing messages
        try:
            while True:
                for socket in sockets:
                    binance_data = socket.recv()

                    coin_prices_data = update_coin_candle_from_binance_data(
                        binance_data)

                    threshold_breaks = is_threshold_breaks(coin_prices_data)

                    if threshold_breaks:
                        # TODO: make_call()
                        print('need call')
                        pass

                # Check if new coin names appear in the database
                    new_currencies = [coin.abbreviation for coin in Coin.objects.all() if coin.abbreviation not in currencies]
                    if new_currencies:
                        print(f"New coins added: {', '.join(new_currencies)}")
                        currencies += new_currencies
                        new_sockets = connect_binance_socket(new_currencies)
                        sockets.extend(new_sockets)

        except KeyboardInterrupt:
            close_binance_sockets(sockets)
        except (ValueError, KeyError) as err:
            print(err)

        # Close sockets when finished
        close_binance_sockets(sockets)

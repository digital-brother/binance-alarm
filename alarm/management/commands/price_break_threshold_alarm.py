from django.core.management.base import BaseCommand

from alarm.models import Coin
from alarm.binance_utils import connect_binance_socket, close_binance_sockets
from alarm.utils import check_if_call_needed, get_binance_data_and_update_coin_candle


class Command(BaseCommand):
    help = 'Starts streaming Binance market data'

    def handle(self, *args, **options):
        # Define the list of currencies and intervals you want to stream
        currencies = [coin.coin_abbreviation for coin in Coin.objects.all()]

        # Connect to Binance exchange
        sockets = connect_binance_socket(currencies)

        # Start processing messages
        try:
            while True:
                for socket in sockets:
                    binance_data = socket.recv()

                    prices = get_binance_data_and_update_coin_candle(
                        binance_data)

                    check_if_call_needed(prices)

                    if check_if_call_needed:
                        # TODO: make_call()
                        pass

                # Check if new coin names appear in the database
                new_currencies = [coin.coin_abbreviation for coin in Coin.objects.all() if
                                  coin.coin_abbreviation not in currencies]
                if new_currencies:
                    currencies += new_currencies
                    new_sockets = connect_binance_socket(new_currencies)
                    sockets.extend(new_sockets)

        except KeyboardInterrupt:
            close_binance_sockets(sockets)
        except (ValueError, KeyError) as err:
            print(err)

        # Close sockets when finished
        close_binance_sockets(sockets)

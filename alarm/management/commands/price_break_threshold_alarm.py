from django.core.management.base import BaseCommand

from alarm.models import Coin
from alarm.utils import connect_binance_socket, process_binance_messages, close_binance_sockets


class Command(BaseCommand):
    help = 'Starts streaming Binance market data'

    def handle(self, *args, **options):
        # Define the list of currencies and intervals you want to stream
        currencies = Coin.objects.values_list('coin_abbreviation', flat=True)
        intervals = ['1s']

        # Connect to Binance exchange
        sockets = connect_binance_socket(currencies, intervals)

        # Start processing messages
        process_binance_messages(sockets)

        # Close sockets when finished
        close_binance_sockets(sockets)

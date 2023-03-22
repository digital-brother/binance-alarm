from django.core.management.base import BaseCommand, CommandError

from alarm.models import Coin
from alarm.utils import get_binance_price_and_analized


class Command(BaseCommand):
    help = 'Get a call a to a specified by a user mobile phones immediately when a specified by a user coins reaches ' \
           'specified by a user prices at Binance '

    def handle(self, *args, **options):
        coin_data = Coin.objects.all()
        for coin in coin_data:
            coin_name = coin.coin_abbreviation
            if coin_name:
                coin = [f'{coin_name}']
                intervals = ['1s']
                get_binance_price_and_analized(coin, intervals)

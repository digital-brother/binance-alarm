from django.core.management.base import BaseCommand, CommandError

from alarm.models import Coin
from alarm.utils import get_binance_price


class Command(BaseCommand):
    help = 'Get a call a to a specified by a user mobile phones immediately when a specified by a user coins reaches ' \
           'specified by a user prices at Binance '

    def handle(self, *args, **options):
        coin_data = Coin.objects.all().order_by('-id')[:1]
        for coin in coin_data:
            coin_name = coin.short_name_coin
            if coin_name:
                interval = ['1s']
                get_binance_price(coin_name, interval)

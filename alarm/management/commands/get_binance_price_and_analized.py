from django.core.management.base import BaseCommand, CommandError

from alarm.models import Coin
from alarm.utils import get_binance_price_and_analized


class Command(BaseCommand):
    help = 'Get a call a to a specified by a user mobile phones immediately when a specified by a user coins reaches ' \
           'specified by a user prices at Binance '

    def handle(self, *args, **options):
        coin_abbreviations = [coin.coin_abbreviation for coin in Coin.objects.all()]
        intervals = ['1s']
        get_binance_price_and_analized(coin_abbreviations, intervals)

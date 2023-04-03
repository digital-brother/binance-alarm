from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, AbstractUser, User
from django.core.exceptions import ValidationError
from django.db import models
from phonenumber_field.modelfields import PhoneNumberField


class Phone(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    number = PhoneNumberField(blank=True, unique=True, region='UA')
    enabled = models.BooleanField(default=False)

    def __str__(self):
        return str(self.number)


class Coin(models.Model):
    phone = models.ForeignKey(Phone, on_delete=models.CASCADE)
    coin_abbreviation = models.CharField(max_length=255)
    threshold = models.DecimalField(max_digits=10, decimal_places=2)
    interval = models.CharField(default='1s', max_length=8, editable=False)

    def __str__(self):
        return str(self.coin_abbreviation)

    def update_or_create_candles(self, current_candle_high_price, current_candle_low_price):
        Candle.objects.update_or_create(
            coin=self,
            defaults={
                'last_high_price': current_candle_high_price,
                'last_low_price': current_candle_low_price,
            },
        )

    def is_valid_coin_abbreviation(self):
        symbols = ["btcusdt",
                   'ethusdt',
                   'xrpusdt',
                   'bnbeth',
                   'adausdt',
                   'dogeusdt',
                   'ethbtc',
                   'dogebtc',
                   'ltcbtc',
                   'bnbbtc',
                   'adabtc',
                   'bchusdt',
                   'ltcusdt',
                   'xmrusdt',
                   'xrpbtc',
                   'eosusdt',
                   'zecusdt',
                   'xlmbtc',
                   'trxusdt',
                   'neousdt',
                   'bnbusdt',
                   'zrxbtc',
                   'linkusdt',
                   'etcusdt',
                   'zrpusdt',
                   'atomusdt',
                   'dashusdt',
                   'xvgbtc',
                   'hotusdt',
                   'qtumbtc',
                   'wavesusdt',
                   'vetusdt',
                   'npxsbtc',
                   'batusdt',
                   'xlmusdt',
                   'nulsbtc',
                   'gtoeth',
                   'bchbtc',
                   'iostusdt',
                   'ltcbnb',
                   'iostbnb',
                   'zenusdt',
                   'adabnb',
                   'xlmeth',
                   'btsusdt',
                   'tusdbtc',
                   'phbbtc',
                   'tusdusdt',
                   'mftbtc',
                   'bntusdt',
                   'mfteth',
                   'dentusdt',
                   'hbarusdt',
                   'denteth',
                   'btcngn',
                   'dgbbtc',
                   'wavesbtc',
                   'hbarbnb',
                   'iotausdt',
                   'oneusdt',
                   'ftmusdt',
                   'maticusdt',
                   'maticbnb',
                   'maticbtc',
                   'maticeth',
                   'maticusdc',
                   'maticpax',
                   'matictusd',
                   'btcusdc',
                   'busdusdc',
                   'btcidrt',
                   'ftmbtc',
                   'ftmusdc',
                   'btcars',
                   'duskusdt',
                   'duskbnb',
                   'xrptusd',
                   'eosbnb',
                   'xlmtusd',
                   'xrpbnb',
                   'xlmbnb',
                   'xmrusd',
                   'lskusdt',
                   'tusdgbp',
                   'btctry',
                   'ltctry',
                   'ftmtusd',
                   'xlmngn',
                   'bchtry',
                   'ftmusdt',
                   'bchngn',
                   'ftmbnb',
                   'hotbnb',
                   'usdtry',
                   'usdttry',
                   'dogeusdt',
                   'dogebnb',
                   'ethtry',
                   'duskbtc',
                   'dusketh',
                   'phbusdt',
                   'phbbnb',
                   'tusdbnb',
                   'eosbusd',
                   'neoeth',
                   'iotabnb',
                   'wavesbnb',
                   'wavesbtc',
                   'stratbtc',
                   'stratusd',
                   'adxusdt',
                   'adaeur',
                   'kavausdt',
                   'trxngn',
                   'kavaeur',
                   'usdceur',
                   'xrpeur',
                   'bcheur',
                   'ltceur',
                   'btcgbp',
                   'ethgbp',
                   'xrpgbp',
                   'bnbpax',
                   'bchgbp',
                   'ltcgbp',
                   'usdcpax',
                   'linketh',
                   'usdcusdt',
                   'waveseth',
                   'linkbtc',
                   'atometh',
                   'usdcngn',
                   'dasheth',
                   'dgbusdt',
                   'btczrx',
                   'dgbbnb',
                   'maticngn',
                   'matictry',
                   'maticdai',
                   'maticrub',
                   'btcuah',
                   'usdcuah',
                   'xrptry',
                   'btctry',
                   'xrpars',
                   'xlmeur',
                   'eosgbp',
                   'dogeeur',
                   'xlmbnb',
                   'ethuahe',
                   'zileth',
                   'btceur',
                   'zilbnb',
                   'usdtzar',
                   'xrpbullusdt',
                   'xrpbearusdt',
                   'tusdbtc',
                   'etcbtc',
                   'etcbnb',
                   'ltcbullusdt',
                   'ltcbearusdt',
                   'ethtusd',
                   'daiusdt',
                   'cvcusdt',
                   'cvceth',
                   'btcngnb',
                   'ethngn',
                   'dntusdt',
                   'dnteth',
                   'sntusdt',
                   'senusdt',
                   'bnteth',
                   'trxngnb',
                   'trxtry',
                   'vibeth',
                   'vibusdt',
                   'mdabtc']
        return self.coin_abbreviation in symbols

    def clean(self):
        super().clean()
        if not self.is_valid_coin_abbreviation():
            raise ValidationError(
                f"{self.coin_abbreviation} is not a valid coin abbreviation. For example, ethusdt or ethbtc")


class Candle(models.Model):
    coin = models.ForeignKey(Coin, on_delete=models.CASCADE)
    last_high_price = models.DecimalField(max_digits=10, decimal_places=2)
    last_low_price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return str(self.coin)

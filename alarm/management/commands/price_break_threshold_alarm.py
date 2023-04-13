import logging
import time

from twilio.rest import Client

from django.core.management.base import BaseCommand

from alarm.binance_utils import connect_binance_socket, close_binance_socket, \
    parse_candle_from_websocket_update
from alarm.models import Threshold, Candle, ThresholdBrake
from alarm.utils import any_of_trade_pair_thresholds_is_broken

logger = logging.getLogger(f'{__name__}')

account_sid = "ACc57a61651083bfb9f4d388b817bd6cd8"
auth_token = "8968fa9cbcee990c3d642f7eb9ab1871"
client = Client(account_sid, auth_token)


class Command(BaseCommand):
    help = 'Gets updates for all trade pairs, analyses if thresholds were broken, ' \
           'makes a call to a user in case of need'

    def handle(self, *args, **options):
        trade_pairs = [threshold.trade_pair for threshold in Threshold.objects.all()]
        socket = connect_binance_socket(trade_pairs)

        try:
            while True:
                binance_data = socket.recv()

                high_price, low_price, trade_pair = parse_candle_from_websocket_update(binance_data)
                Candle.refresh_candle_data(trade_pair, high_price, low_price)

                if any_of_trade_pair_thresholds_is_broken(trade_pair):
                    threshold_brakes = ThresholdBrake.objects.all()

                    for threshold_brake in threshold_brakes:
                        threshold = threshold_brake.threshold
                        trade_pair = threshold.trade_pair
                        price = ', '.join([f'{threshold_brake.price}$' for threshold_brake in
                                           Threshold.objects.filter(trade_pair=trade_pair)])
                        candle = Candle.objects.filter(trade_pair=trade_pair).order_by(
                            '-modified').last()  # Get the latest candle
                        # Check if the candle exists before accessing its high price
                        high_price = candle.high_price if candle else None
                        message = f"<Response><Say>Attention! Trade pair {trade_pair} has broken thresholds {price} and current price is {high_price}$</Say></Response> "

                        call = client.calls.create(
                            twiml=message,
                            to='+380933330898',
                            from_='+15075858335'
                        )

                        # Check the call status
                        if call.status == 'completed':
                            # Sleep for 15 minutes
                            time.sleep(900)
                        elif call.status == 'busy' or call.status == 'failed':
                            # Sleep for 1 minute and create a new call
                            time.sleep(60)
                            call = client.calls.create(
                                twiml=message,
                                to='+380933330898',
                                from_='+15075858335'
                            )
                        else:
                            # Try to call the user every minute for 15 minutes
                            for i in range(15):
                                time.sleep(60)
                                call = call = client.calls.create(
                                    twiml=message,
                                    to='+380933330898',
                                    from_='+15075858335'
                                )
                                if call.status == 'completed':
                                    break
                                elif i == 14:
                                    # Maximum attempts reached, exit the loop
                                    break

                    logger.info('need call')

                # Check if new coin names appear in the database
                new_trade_pairs = [threshold.trade_pair for threshold in Threshold.objects.all()
                                   if threshold.trade_pair not in trade_pairs]
                if new_trade_pairs:
                    logger.info(f"New trade pairs added: {new_trade_pairs}")
                    trade_pairs += new_trade_pairs
                    new_socket = connect_binance_socket(trade_pairs)
                    socket = new_socket

        except KeyboardInterrupt:
            close_binance_socket(socket)
        except (ValueError, KeyError) as err:
            logger.error(err)

        close_binance_socket(socket)

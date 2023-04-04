import requests


def get_valid_list_of_symbols():
    BINANCE_API_URL = "https://api.binance.com/api/v3/exchangeInfo"
    response = requests.get(BINANCE_API_URL)

    if response.status_code == 200:
        valid_list_of_symbols = [symbol['symbol'].lower() for symbol in response.json()['symbols']]
        return valid_list_of_symbols
    else:
        return []

import websocket
import ssl


def my_view(request):
    if request.method == 'GET':

        def on_open(ws, currency, interval):
            print(f'Streaming K-line data for {currency} at {interval} intervals...')

        def on_message(ws, message):
            print(message)

        def on_error(ws, error):
            print(error)

        def on_close(ws, close_status_code, close_msg):
            print("###Close Streaming" + close_msg)

        def streamKline(currencies, intervals):
            websocket.enableTrace(False)
            sockets = [f'wss://stream.binance.com:9443/ws/{currency}@kline_{interval}' for currency, interval in
                       zip(currencies, intervals)]

            ws_list = []
            for socket in sockets:
                ws = websocket.create_connection(socket, sslopt={'cert_reqs': ssl.CERT_NONE})
                ws.on_open = on_open
                ws.on_message = on_message
                ws.on_error = on_error
                ws.on_close = on_close
                ws_list.append(ws)

            try:
                while True:
                    for ws in ws_list:
                        message = ws.recv()
                        on_message(ws, message)
            except KeyboardInterrupt:
                for i, ws in enumerate(ws_list):
                    on_close(ws, '', close_msg=f' {currencies[i]}')
                    ws.close()
            except Exception as e:
                print(f'An error occurred: {e}')

        currencies = ['btcusdt', 'ethusdt', 'bnbusdt']
        intervals = ['1s', '1s', '1s']
        streamKline(currencies, intervals)

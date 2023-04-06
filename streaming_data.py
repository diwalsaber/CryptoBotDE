import websocket
import json

def on_open(ws):
    print("### opened ###")

def on_message(ws, message):
    print(message)

def on_error(ws, error):
    print(error)

def on_close(ws):
    print("### closed ###")

endpoint = "wss://stream.binance.com:9443/ws/btcusdt@kline_1m"

ws = websocket.WebSocketApp(endpoint,
                            on_open=on_open,
                            on_message=on_message,
                            on_error=on_error,
                            on_close=on_close)

ws.run_forever()
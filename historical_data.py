from binance.client import Client
import csv


api_key = "VOTRE_API_KEY"
api_secret = "VOTRE_API_SECRET"

client = Client(api_key, api_secret)

symbol = "BTCUSDT"
interval = Client.KLINE_INTERVAL_1HOUR # 4 heures

# Récupérer l'historique des bougies (candlesticks) avec un intervalle de 4 heures
#candles = client.get_klines(symbol=symbol, interval=interval)
candles = client.get_historical_klines(symbol=symbol, interval=interval, start_str="1 Jan, 2017", end_str="1 Apr, 2023")


with open("candles.csv", "w", newline="") as f:
    csv_writer = csv.writer(f)

    csv_writer.writerow(["Open Time", "Open", "High", "Low", "Close", "Volume", "Close Time"])

    # Ajouter les bougies à notre fichier CSV
    for candle in candles:
        open_times = candle[0]
        open_price = candle[1]
        high_price = candle[2]
        low_price = candle[3]
        close_price = candle[4]
        volume = candle[5]
        close_time = candle[6]

        csv_writer.writerow([open_times, open_price, high_price, low_price, close_price, volume, close_time])

#print(type(candles))

# Afficher les bougies
# for candle in candles:
#     open_time, open_price, high_price, low_price, close_price, volume, close_time, _, _, _, _, _ = candle
#     print(f"Open Time: {open_time}, Open: {open_price}, High: {high_price}, Low: {low_price}, Close: {close_price}, Volume: {volume}, Close Time: {close_time}")

# print(candles[0][:])


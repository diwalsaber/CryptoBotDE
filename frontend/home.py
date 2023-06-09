import streamlit as st
import requests
from binance.client import Client

# deployement on local machine
#BACKEND = "http://127.0.0.1:8000"

# deployement on docker container
BACKEND = "http://fastapi:8001"

# Initialiser le client Binance
client = Client(api_key='your_api_key', api_secret='your_api_secret')

def get_klines_close_prices(symbol: str, interval: str, count: int):
    """
    Récupère les derniers prix de clôture pour un symbole donné à partir de l'API Binance.

    Args:
    symbol (str): Le symbole de la paire de devises (par exemple "BTCUSDT").
    interval (str): L'intervalle des klines (par exemple Client.KLINE_INTERVAL_1DAY).
    count (int): Le nombre de klines à récupérer.

    Returns:
    list[float]: La liste des derniers prix de clôture.
    """
    klines = client.get_klines(symbol=symbol, interval=interval)
    return [float(kline[4]) for kline in klines[-count:]]

def get_close_prices(nb_day: int):
    """
    Récupère les derniers prix de clôture depuis le backend.

    Returns:
    list[float]: La liste des derniers prix de clôture.
    """
    response = requests.get(BACKEND + "/prices", params={"nb_day": nb_day})
    response.raise_for_status()
    return response.json()['prices']

# Récupérer les derniers prix de clôture depuis le backend avec un count de 3
close_prices = get_close_prices(nb_day=3)

def make_prediction(data):
    """
    Fait une prédiction en utilisant le backend.

    Args:
    data (list[float]): Les données à utiliser pour la prédiction.

    Returns:
    list[float]: La prédiction renvoyée par le backend.
    """
    payload = {"data": data}
    response = requests.post(BACKEND + "/predict", json=payload)
    response.raise_for_status()
    return response.json()['prediction']

# Interface utilisateur Streamlit
st.title('Prévision du prix du BTC')

# Récupérer les derniers prix de clôture
last_3_close_prices = get_klines_close_prices("BTCUSDT", Client.KLINE_INTERVAL_1DAY, 3)

# Créer un bouton pour prédire le prix
if st.button("Predict"):
    prediction = make_prediction(close_prices)
    st.write('Prédiction :', prediction)
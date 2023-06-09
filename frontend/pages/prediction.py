import streamlit as st
import requests
from binance.client import Client

# URL du backend pour la prédiction
BACKEND = "http://fastapi:8001"

# Initialiser le client Binance
client = Client(api_key='your_api_key', api_secret='your_api_secret')

st.set_option('deprecation.showPyplotGlobalUse', False)
st.set_page_config(page_title="prediction", page_icon="🔮", layout="wide")


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


# Créer un bouton pour prédire le prix
if st.button("Predict"):
    prediction = make_prediction(close_prices)
    st.write('Prédiction :', prediction)
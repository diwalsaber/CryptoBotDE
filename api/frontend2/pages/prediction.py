import streamlit as st
import requests
from binance.client import Client

from cryptobot.common.cryptoutils import get_env_value_fallback

# URL du backend pour la prédiction
BACKEND = f"""http://{get_env_value_fallback('API_HOST', 'localhost')}:{get_env_value_fallback('API_PORT',8000)}"""
TOKEN_KEY = f"{get_env_value_fallback('API_KEY')}"
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
    response = requests.get(BACKEND + "/prices", params={"nb_day": nb_day}, headers={'Authorization': f'Bearer {TOKEN_KEY}'})
    print(response)
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
    response = requests.post(BACKEND + "/model/predict", json=payload, headers={'Authorization': f'Bearer {TOKEN_KEY}'})
    print(response)
    response.raise_for_status()
    return response.json()['prediction']

def get_current_price():
    response = requests.get(BACKEND + "/avg_price_24h", headers={'Authorization': f'Bearer {TOKEN_KEY}'})
    print(response)
    return response.json()["avg_price_24h"]

# Une fonction qui demande le dernier prix du BTC
def get_latest_price():
    """
    Récupère le dernier prix en temps réel depuis le backend.

    Returns:
    float: Le dernier prix en temps réel.
    """
    response = requests.get(BACKEND + "/latest_price", headers={'Authorization': f'Bearer {TOKEN_KEY}'})
    print(response)
    response.raise_for_status()
    return response.json()['latest_price']

try:
    st.title('Prévision du prix du BTC')

    current_price = get_current_price()
    st.markdown(f'Prix moyen sur 24h : <span style="font-family:Monospace; color:black; font-weight:bold; background-color:#f2f2f2; padding:5px;">{current_price:.2f}</span>', unsafe_allow_html=True)

    # Récupérez le dernier prix en temps réel depuis le backend
    latest_price = get_latest_price()
    if float(latest_price) > float(current_price):
        st.markdown(f'Prix actuel : <span style="font-family:Monospace; color:#00ff00; font-weight:bold; background-color:#f2f2f2; padding:5px;">{latest_price:.2f}</span>', unsafe_allow_html=True)
        st.markdown('_Le prix est vert car il a augmenté par rapport au prix moyen des dernières 24h._', unsafe_allow_html=True)
    else:
        st.markdown(f'Prix actuel : <span style="font-family:Monospace; color:#ff0000; font-weight:bold; background-color:#f2f2f2; padding:5px;">{latest_price:.2f}</span>', unsafe_allow_html=True)
        st.markdown('_Le prix est en rouge car il a diminué par rapport au prix moyen des dernières 24h._', unsafe_allow_html=True)

    # Créer un bouton pour prédire le prix
    if st.button("Prediction"):
        prediction = make_prediction(close_prices)
        if float(prediction) > float(latest_price):
            st.markdown(f'Prediction +24h : <span style="font-family:Monospace; color:#00ff00; font-weight:bold; background-color:#f2f2f2; padding:5px;">{prediction:.2f}</span>', unsafe_allow_html=True)
            st.markdown('_La prédiction est en vert car elle est supérieure au dernier prix enregistré._', unsafe_allow_html=True)
        else:
            st.markdown(f'Prediction +24h : <span style="font-family:Monospace; color:#ff0000; font-weight:bold; background-color:#f2f2f2; padding:5px;">{prediction:.2f}</span>', unsafe_allow_html=True)
            st.markdown('_La prédiction est en rouge car elle est inférieure au dernier prix enregistré._', unsafe_allow_html=True)
except Exception as e:
    st.write(f"<div>Somthing went wrong!:{e}</div>")
    print(e)
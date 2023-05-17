import streamlit as st
import pandas as pd
import requests

# Deployement on docker
#BACKEND = "http://fastapi:8000/predict"

# Deployement on local machine
BACKEND = "http://localhost:8000/predict"

# Fonction pour faire une prédiction
def make_prediction(data):
    response = requests.post(BACKEND, json={'data': data})
    prediction = response.json()['prediction']
    return prediction

# Interface utilisateur Streamlit
st.title('Prévision du prix du BTC')

# Télécharger les données
uploaded_file = st.file_uploader("Upload CSV", type=['csv'])
if uploaded_file is not None:
    data = pd.read_csv(uploaded_file, usecols=["open_time", "close_price"]).tail(3)
    st.write(data)

    # Bouton pour faire une prédiction
    if st.button('Prédire'):
        prediction = make_prediction(data.values.tolist())
        st.write('Prédiction :', prediction)
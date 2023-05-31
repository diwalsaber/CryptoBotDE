import streamlit as st
import pandas as pd
import requests


# Deployement on local machine
BACKEND = "http://localhost:8000"


st.set_page_config(page_title="Information LSTM", page_icon="💻")

st.markdown("# Information sur l'algorithme LSTM 💻")
st.sidebar.success("Page: Information LSTM")
st.write(
    "Cette page affiche les informations sur l'algorithme LSTM (modèle de réseau de neurones) \
    utilisées pour la prédiction du cours BTC/USDT.") 

st.write("")
st.write("**Informations sur le modèle:**")
response = requests.get(BACKEND + '/model_summary')
data_model = pd.DataFrame(response.json())
st.write(data_model)




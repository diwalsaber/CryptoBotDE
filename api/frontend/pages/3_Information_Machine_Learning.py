import streamlit as st
import pandas as pd
import requests


# Deployement on local machine
BACKEND = "http://localhost:8000"


st.set_page_config(page_title="Information Machine Learning", page_icon="💻")

st.markdown("# Information sur l'algorithme de Machine Learning 💻")
st.sidebar.success("Page: Information Machine Learning")
st.write(
    "Cette page affiche les informations sur l'algorithme de Machine Learning \
    utilisées pour la prédiction du cours BTC/USDT. \
    \nAinsi que le score du modèle indiquant l'erreur moyenne sur la prédiction. \
    \nLe modèle utilisé est un modèle LSTM, modèle de réseau de neurones."
)

st.write("")
st.write("**Informations sur le modèle:**")
response = requests.get(BACKEND + '/model_summary')
data_model = pd.DataFrame(response.json())
st.write(data_model)

st.write("")
st.write("**Score RMSE du modèle:**")
response = requests.get(BACKEND + '/score')
score_train = response.json()['RMSE_score_train_data']
score_test = response.json()['RMSE_score_test_data']
st.write("Score RMSE sur le jeux d'entrainement: ", score_train)
st.write("Score RMSE sur le jeux de test: ", score_test)




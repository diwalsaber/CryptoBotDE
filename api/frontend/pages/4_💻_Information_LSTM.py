import streamlit as st
import pandas as pd
import requests


# Deployement on local machine
BACKEND = "http://localhost:8000"
TOKEN_KEY = ""
identification = False


# Récupération sur le modèle active 
def get_info():
    # Récupération info modèle
    response = requests.post(BACKEND + '/model/info?symbol=BTCUSDT&interval=1 day', json={},
                            headers={'Authorization': TOKEN_KEY})
    data = response.json()
    info_list = []
    for cle, valeur in data.items():
        info_list.append({'Parametre': cle, 'Valeur': f'{valeur}'})

    return info_list


st.set_page_config(page_title="Information LSTM", page_icon="💻")

st.markdown("# Information sur l'algorithme LSTM 💻")
st.sidebar.success("Page: Information LSTM")
st.write(
    "Cette page affiche les informations sur l'algorithme LSTM (modèle de réseau de neurones) \
    utilisées pour la prédiction du cours BTC/USDT.") 


if ('token_key' not in st.session_state) or (st.session_state['token_key'] == ""):
    st.write("")
    st.write("Merci de vous identifiez dans la page Identification!!!")
    identification = False
else:
    TOKEN_KEY = "Bearer " + st.session_state['token_key']
    identification = True

if identification:
    st.write("")
    st.write("**Informations sur le modèle:**")
    info_model = get_info()
    data_model = pd.DataFrame(info_model)
    st.dataframe(data_model, height=530, width=1000)
    



import streamlit as st
import pandas as pd
import requests
import plotly.graph_objects as go
from datetime import datetime

from cryptobot.common.cryptoutils import get_env_value_fallback

# Deployement on local machine
BACKEND = f"""http://{get_env_value_fallback('API_HOST', 'localhost')}:{get_env_value_fallback('API_PORT',8000)}"""
TOKEN_KEY = f"{get_env_value_fallback('API_KEY')}"
identification = False

# Fonction pour faire une prédiction
def make_prediction(nb_future):
    # Récupération prédiction via API en envoyant les valeurs pour la prédiction
    response = requests.post(BACKEND + '/model/predict?symbol=BTCUSDT&interval=1 day&nb_future={}'.format(nb_future), json={},
                            headers={'Authorization': TOKEN_KEY})
    return response.json()

# Fonction pour récupérer les infos du modèle, en particulier le lookback
def get_lookback_model():
    # Récuparation info modèle
    response = requests.post(BACKEND + '/model/info?symbol=BTCUSDT&interval=1 day', json={},
                            headers={'Authorization': TOKEN_KEY})
    lookback = response.json()['lookback']
    return lookback

# Fonction pour récupérer les infos du modèle, en particulier les scores RMSE
def get_rmse_score_model():
    # Récuparation info modèle
    response = requests.post(BACKEND + '/model/info?symbol=BTCUSDT&interval=1 day', json={},
                            headers={'Authorization': TOKEN_KEY})
    score = response.json()['scores']
    score = score[1:-1].split(',')
    score_train = score[0].split(':')[1]
    score_test = score[1].split(':')[1]
    return score_train, score_test

st.set_page_config(page_title="Prediction Cours", page_icon="🔮")

st.markdown("# Prediction du cours BTC/USDT 🔮")
st.sidebar.success("Page: Prediction Cours")
st.write(
    "Cette page affiche une prédiction de la valeur du BTC/USDT. \
    \nAvec le score RMSE du modèle indiquant l'erreur moyenne sur la prédiction. \
    \nOn peut choisir le nombre de jours pour la prediction dans le futur.")

if ('token_key' not in st.session_state) or (st.session_state['token_key'] == ""):
    st.write("")
    st.write("Merci de vous identifiez dans la page Identification!!!")
    identification = False
else:
    TOKEN_KEY = "Bearer " + st.session_state['token_key']
    identification = True

if identification:
    st.write("")
    st.write("**Dernières données BTC/USDT utilisées pour la prédiction:**")
    # Récupération des dernières valeurs du BTC/USDT via API
    lookback = get_lookback_model()
    response = requests.get(BACKEND + '/data?nb_records={}&interval="1 day"&mov_avg=30'.format(lookback), 
                            headers={'Authorization': TOKEN_KEY})
    data = pd.DataFrame(response.json())

    data['date'] = data['close_time'].apply(lambda row: datetime.utcfromtimestamp(row/1000000000).strftime('%Y-%m-%d'))
    data = data[['date', 'close_price']]

    # Affichage du tableau contenant les dernières valeurs utilisés pour la prédiction
    st.write(data)

    st.write("")
    plot_spot1 = st.empty()
    plot_spot2 = st.empty()
    plot_spot3 = st.empty()
    plot_spot4 = st.empty()

st.sidebar.write("")
option_nb_future = st.sidebar.slider("Nombre de jours à prédire:", 1, 3, 1)

st.sidebar.write("")
# Bouton pour faire une prédiction
if st.sidebar.button('Prédire', disabled=not identification):
    sequence_values = data['close_price'].values.reshape(-1,1).flatten().tolist()
    last_date = data['date'].values.reshape(-1,1).flatten().tolist()[-1]
    prediction = make_prediction(option_nb_future)
    data_prediction = pd.DataFrame(prediction)
    with plot_spot1:
        st.write("**Prédiction:**")
    with plot_spot2:
        st.write(data_prediction)
    with plot_spot3:
        score_train, score_test = get_rmse_score_model()
        st.write("\n**Score RMSE du modèle:** \
                \nScore RMSE sur le jeux d'entrainement: {} \
                \nScore RMSE sur le jeux de test: {}".format(score_train, score_test))
    with plot_spot4:
        current_value = data['close_price'].iloc[-1]
        prediction = data_prediction['prediction'].iloc[0]
        current_value_80 = current_value*0.8
        current_value_95 = current_value*0.95
        current_value_105 = current_value*1.05
        current_value_120 = current_value*1.2
        fig = go.Figure(go.Indicator(
            mode = "number+gauge+delta", value = prediction,
            domain = {'x': [0, 1], 'y': [0, 1]},
            delta = {'reference': current_value, 'position': "top"},
            title = {'text':"Indicateur d\'achat"},
            gauge = {
                #'shape': "bullet",
                'shape': "angular",
                'axis': {'range': [current_value_80, current_value_120]},
                'bgcolor': "white",
                'steps': [
                    {'range': [current_value_80, current_value_95], 'color': "red"},
                    {'range': [current_value_95, current_value_105], 'color': "yellow"},
                    {'range': [current_value_105, current_value_120], 'color': "green"}],
                'bar': {'color': "royalblue"}}))
        fig.update_layout(height = 350)
        st.plotly_chart(fig)

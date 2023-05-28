import streamlit as st
import pandas as pd
import requests
import plotly.graph_objects as go


# Deployement on local machine
BACKEND = "http://localhost:8000"

# Fonction pour faire une prédiction
def make_prediction(data, date, nb_future):
    # Récupération prédiction via API en envoyant les valeurs pour la prédiction
    response = requests.post(BACKEND + '/predict3?nb_future={}'.format(nb_future), json={'data': data, 'date': date, 'last_values': True})
    return response.json()


st.set_page_config(page_title="Prediction Cours", page_icon="💻")

st.markdown("# Prediction de la crypto BTC/USDT 💻")
st.sidebar.success("Page: Prediction Cours")
st.write(
    """Cette page affiche une prédiction de la valeur du BTC/USDT.
    On peut choisir le nombre de jours pour la prediction dans le futur"""
)

st.write("")
st.write("Dernières données BTC/USDT utilisées pour la prédiction:")
# Récupération des 3 dernières valeurs du BTC/USDT via API
response = requests.get(BACKEND + '/values')
data = pd.DataFrame(response.json())

# Affichage du tableau contenant les 3 dernières valeurs utilisés pour la prédiction
st.write(data)

st.write("")
plot_spot1 = st.empty()
plot_spot2 = st.empty()
st.write("")
plot_spot3 = st.empty()

st.sidebar.write("")
option_nb_future = st.sidebar.slider("Nombre de jours pour la prediction dans le futur:", 1, 3, 1)

st.sidebar.write("")
# Bouton pour faire une prédiction
if st.sidebar.button('Prédire'):
    prediction = make_prediction(response.json()['close_price'], response.json()['close_time'][-1], option_nb_future)
    data_prediction = pd.DataFrame(prediction)
    with plot_spot1:
        st.write("Prédiction:")
    with plot_spot2:
        st.write(data_prediction)
    with plot_spot3:
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

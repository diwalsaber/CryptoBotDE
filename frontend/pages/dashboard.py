import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
import streamlit as st
import pandas as pd

BACKEND = "http://localhost:8000"

def plot_candlestick(nb_days, moving_avg_period=7):
    response = requests.get(BACKEND + '/ohlcv', params={'nb_days': nb_days})
    data = pd.DataFrame(response.json())
    data['day'] = pd.to_datetime(data['day'])
    data['moving_average'] = data['close'].rolling(window=moving_avg_period).mean()

    # Créer le graphique de bougies
    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=("Prix du Bitcoin (USD)", "Volume d\'échange du Bitcoin"),
        shared_xaxes=True,
        vertical_spacing =0.3
    )
    fig.add_trace(go.Candlestick(
        name='Bougie',
        x=data['day'],
        open=data['open'],
        high=data['high'],
        low=data['low'],
        close=data['close']
    ), row=1, col=1)

    # Créer le graphique des Volumes d'échanges
    fig.add_trace(go.Bar(name='Volume', x=data['day'], y=data['volume']), row=2, col=1)

    fig.update_layout(
        title=f'Historique des prix du Bitcoin des {len(data)} derniers jours',
        yaxis_title='Prix du Bitcoin (USD)',
        xaxis_title='Date',
        width=800, height=1000
    )

    # Ajouter la moyenne mobile
    fig.add_trace(go.Scatter(x=data['day'], y=data['close'].rolling(moving_avg_period).mean(),
                              name=f'MA {moving_avg_period} days',
                              line={'color': 'royalblue', 'width': 2}))

    st.plotly_chart(fig)

def app():
    st.title("Dashboard des prix du BTC")

    # Récupérer le nombre de jours à afficher
    nb_days = st.slider("Nombre de jours à afficher", min_value=30, max_value=500, value=365, step=10)
    # Récupérer la période de la moyenne mobile
    moving_avg_period = st.slider("Période de la moyenne mobile", min_value=3, max_value=30, value=7, step=1)

    # Afficher le graphique
    plot_candlestick(nb_days, moving_avg_period)


if __name__ == "__main__":
    app()


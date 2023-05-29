import streamlit as st
import pandas as pd
import requests
import plotly_express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import date


# Deployement on local machine
BACKEND = "http://localhost:8000"

def compute_nb_records(period = 'All', interval = '1 day'):
    """Compute the number of records to retrieve from the database
    Teh number of records depends on the period and the interval

    Args:
        period: period to display related to the cuurent date
        interval: interval between each records to be displayed

    Return: the number of records
    """
    nb_day = 1
    if interval == '3 days':
        nb_day = 3
    elif interval == '1 week':
        nb_day = 7
    elif interval == '1 month':
        nb_day = 30
    else:
        nb_day = 1

    period_day = 365
    if period == '3 days':
        period_day = 3
    elif period == '1 week':
        period_day = 7
    elif period == '1 month':
        period_day = 30
    elif period == '3 months':
        period_day = 3*30
    elif period == '1 year':
        period_day = 365
    elif period == '3 years':
        period_day = 3*365
    else:
        date1 = date(2017, 8, 17)
        date2 = date.today()
        period_day = int((date2-date1).days)

    # the number of records should be ont at least
    nb_records = period_day // nb_day
    if nb_records == 0:
        nb_records = 1

    return nb_records

# Fonction pour mettre à jour le dataframe pour les affichages
@st.cache_data
def update_dataframe(interval = "1 day", mov_avg = 10, period = "All"):
    """Update/Load the dataframe from the database depending on the interval, and the period
    And compute the moving average on the close price

    Args:
        interval: interval between each records to be displayed
        mov_avg: value of the moving average
        period: period to display related to the cuurent date

    Return:
        a dataframe according the parameters above
    """
    nb_records = compute_nb_records(period, interval)

    response = requests.get(BACKEND + '/data?nb_records={}&interval="{}"&mov_avg={}'.format(nb_records, interval, mov_avg))
    df = pd.DataFrame(response.json())

    df['open_time'] = pd.to_datetime(df['open_time'])
    df['close_time'] = pd.to_datetime(df['close_time'])

    return df


st.set_page_config(page_title="Affichage cours crypto", page_icon="📈")

st.markdown("# Affichage du cours de la crypto BTC/USDT 📈")
st.sidebar.success("Page: Affichage Cours")
st.write(
    "Affichage du cours pour la crypto BTC/USDT avec un tableau contenant les données journaliers \
    et un graphique pour voir l'évolution du cours, ainsi que la moyenne mobile. \
    \nLe graphique affiché est paramètrable.\
    "
)

st.write("")
st.write("**Tableau:**")

# Chargement du dataframe
df = update_dataframe()

# Affichage tableau cours BTC/USDT
st.write(df)

st.sidebar.write("")
# Affichage combobox pour choix interval et slider pour la valeur de la moyenne mobile
period_choice = ['3 days', '1 week', '1 month', '3 months', '1 year', '5 years', 'All']
index_ix = period_choice.index('All')
option_period = st.sidebar.selectbox(
            'Valeur période:',
            period_choice,
            index = index_ix
        )
st.sidebar.write("")

interval_choice = ['1 day', '3 days', '1 week', '1 month']
option_interval = st.sidebar.selectbox(
            'Valeur intervalle:',
            interval_choice
        )
st.sidebar.write("")

#st.sidebar.write("Veuillez choisir la valeur de la moyenne mobile à afficher:")
option_avg = st.sidebar.slider("Valeur moyenne mobile:", 1, 120, 30)

st.write("")
st.write("**Graphique:**")
#plot_spot1 = st.empty()
plot_spot2 = st.empty()

if st.sidebar.button('Affichage graphique'):
    df = update_dataframe(option_interval, option_avg, option_period)
    #with plot_spot1:
    #    fig1 = px.line(df, x='open_time', y=['close_price', 'moving_average'], title='Prix BTC/USDT avec moyenne mobile')
    #    fig1.update_layout(width=800, height=400, xaxis=dict(title_text=""), yaxis=dict(title_text="prix USDT"), title={'x': 0.5, 'xanchor': 'center'})
    #    st.plotly_chart(fig1)
    with plot_spot2:
        fig2 = make_subplots(
                    rows=2, cols=1,
                    subplot_titles=("Prix BTC/USDT", "Volume BTC/USDT"),
                    shared_xaxes=True,
                    vertical_spacing =0.3)# tune this value until the two charts don't overlap
        fig2.add_trace(go.Candlestick(
                        name = 'Bougie',
                        x=df['open_time'],
                        open=df['open_price'],
                        high=df['high_price'],
                        low=df['low_price'],
                        close=df['close_price']), row=1, col=1)
        fig2.add_trace(go.Bar(name = 'Volume', x=df['open_time'], y=df['base_volume']), row=2, col=1)
        fig2.update_layout(width=800, height=1000)
        ema_trace = go.Scatter(x=df['open_time'], y=df['moving_average'], 
                               mode='lines', name='Moyenne mobile', line={'color': 'royalblue', 'width': 3})
        fig2.add_trace(ema_trace)
        st.plotly_chart(fig2)











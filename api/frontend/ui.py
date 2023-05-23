import streamlit as st
import pandas as pd
import requests
import psycopg2 as pg
import plotly_express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots


# Deployement on docker
#BACKEND = "http://fastapi:8000/predict"

# Deployement on local machine
BACKEND = "http://localhost:8000"


def load_data_from_Postgres(query, host='localhost', port=5432, dbname='postgres', user='postgres', password='postgres'):
    """Load the dataset from a PostgreSQL TimescaleDB table using a SQL query.

    Args:
        query (str): The SQL query to load the data.
        host (str, optional): The database server address. Defaults to 'localhost'.
        port (int, optional): The database server port. Defaults to 5432.
        dbname (str, optional): The name of the database. Defaults to 'postgres'.
        user (str, optional): The username used to connect to the database. Defaults to 'postgres'.
        password (str, optional): The password used to connect to the database. Defaults to 'postgres'.

    Returns:
        pandas.DataFrame: The loaded dataset from Timescale DB as a pandas DataFrame.
    """
    connection_params = {
        'host': host,
        'port': port,
        'dbname': dbname,
        'user': user,
        'password': password
    }

    with pg.connect(**connection_params) as conn:
        data = pd.read_sql_query(query, conn)

    return data


# Fonction pour faire une prédiction
def make_prediction(data):
    # Récupération prédiction via API en envoyant les valeurs pour la prédiction
    response = requests.post(BACKEND + '/predict', json={'data': data})
    prediction = response.json()['prediction']
    prediction = prediction[0]
    return prediction

# Fonction pour mettre à jour le dataframe pour les affichages
@st.cache_data
def update_dataframe(interval = "1 day", mov_avg = 30):
    sql_query = " \
      SELECT a.*, AVG(close_price) OVER(ORDER BY open_time ROWS BETWEEN 29 PRECEDING AND CURRENT ROW) AS mov_avg_close_price \
      FROM \
        (SELECT time_bucket('1 day', opentime) AS open_time, \
                first(openprice, opentime) AS open_price, \
                max(highprice) AS high_price, \
                min(lowprice) AS low_price, \
                last(closeprice, closetime) AS close_price, \
                sum(basevolume) AS base_volume, \
                max(closetime) AS close_time \
        FROM candlestickhistorical \
        GROUP BY open_time \
        ORDER BY open_time \
        ) AS a; \
    ".format(interval, str(mov_avg-1))
    df = load_data_from_Postgres(sql_query)
    
    return df


st.title('Cours du BTC/USDT')
# Chargement données BTC/USDT
#interval = "1 day"
#mov_avg = 30
#sql_query = " \
#      SELECT a.*, AVG(close_price) OVER(ORDER BY open_time ROWS BETWEEN 29 PRECEDING AND CURRENT ROW) AS mov_avg_close_price \
#      FROM \
#        (SELECT time_bucket('1 day', opentime) AS open_time, \
#                first(openprice, opentime) AS open_price, \
#                max(highprice) AS high_price, \
#                min(lowprice) AS low_price, \
#                last(closeprice, closetime) AS close_price, \
#                sum(basevolume) AS base_volume, \
#                max(closetime) AS close_time \
#        FROM candlestickhistorical \
#        GROUP BY open_time \
#        ORDER BY open_time \
#        ) AS a; \
#".format(interval, str(mov_avg-1))
#df = load_data_from_Postgres(sql_query)

df = update_dataframe()

# Affichage tableau cours BTC/USDT
st.write(df)

# Affichage combobox pour choix interval et slider pour la valeur de la moyenne mobile
interval_choice = ['1 day', '3 day', '1 week', '1 month']
option_interval = st.selectbox(
            'Veuillez choisir l\'intervalle:',
            interval_choice
        )
st.write("")
st.write("Veuillez choisir la valeur de la moyenne mobile:")
option_avg = st.slider("Valeur moyenne mobile", 0, 100, 10)

# Bouton pour mise à jour dataframe et affichage
# mais ca ne marche pas
if st.button('Mise à jour affichage'):
    df = update_dataframe(option_interval, option_avg)

df['open_time'] = pd.to_datetime(df['open_time'])
# Affichage cours close_price et moyenne mobile 30 jours
fig1 = px.line(df, x='open_time', y=['close_price', 'mov_avg_close_price'], title='Prix BTC/USDT avec moyenne mobile')
fig1.update_layout(width=800, height=400, xaxis=dict(title_text=""), yaxis=dict(title_text="prix USDT"))
ts_chart1 = st.plotly_chart(fig1)

##Affichage des volumes
#fig3 = px.bar(df, x='open_time', y='base_volume', title='Volume BTC/USDT')
#fig3.update_layout(width=800, height=400, xaxis=dict(title_text=""), yaxis=dict(title_text="volume"))
#barplot_chart = st.write(fig3)
#
## Affichage cours en format chandelier
#fig2 = go.Figure(data=[go.Candlestick(x=df['open_time'],
#                open=df['open_price'],
#                high=df['high_price'],
#                low=df['low_price'],
#                close=df['close_price'])])
#fig2.update_layout(width=800, height=400, title='Price BTC/USDT (Candlestick)')
#ts_chart2 = st.plotly_chart(fig2)
#
#fig4 = go.Figure(data=[go.Bar(x=df['open_time'], y=df['base_volume'])])
#fig4.update_layout(width=800, height=400, title='Volume BTC/USDT')
#ts_chart3 = st.plotly_chart(fig4)

# Affichage cours en format chandelier avec volume
fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=("Prix BTC/USDT (format bougie)", "Volume BTC/USDT"),
            shared_xaxes=True,
            vertical_spacing =0.3)# tune this value until the two charts don't overlap
fig.add_trace(go.Candlestick(
                name = 'Bougie',
                x=df['open_time'],
                open=df['open_price'],
                high=df['high_price'],
                low=df['low_price'],
                close=df['close_price']), row=1, col=1)
fig.add_trace(go.Bar(name = 'Volume', x=df['open_time'], y=df['base_volume']), row=2, col=1)
fig.update_layout(width=800, height=800)
ts_chart4 = st.plotly_chart(fig)


# Interface utilisateur Streamlit pour prediction
st.title('Prévision du prix du BTC')

# Télécharger les données via CSV
#uploaded_file = st.file_uploader("Upload CSV", type=['csv'])
#if uploaded_file is not None:
#data = pd.read_csv(uploaded_file, usecols=["open_time", "close_price"]).tail(3)

# Récupération des 3 dernières valeurs du BTC/USDT via API
response = requests.get(BACKEND + '/values')
data = pd.DataFrame(response.json())
data = data.rename(columns={'date_sequence': 'date', 'sequence': 'close_price'})

# Affichage du tableau contenant les 3 dernières valeurs utilisés pour la prédiction
st.write(data)

# Bouton pour faire une prédiction
if st.button('Prédire'):
    #prediction = make_prediction(data['close_price'].values.tolist())
    prediction = make_prediction(response.json()['sequence'])
    st.write('Prédiction :', prediction)


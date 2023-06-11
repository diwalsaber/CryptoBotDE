from fastapi import FastAPI, HTTPException, WebSocket
from pydantic import BaseModel
from keras.models import load_model
from datetime import timedelta
import psycopg2 as pg
import pandas as pd
import joblib
from binance import AsyncClient, BinanceSocketManager

# Charger le modèle de prédiction et le scaler
model = load_model('lstm.h5')
scaler = joblib.load('scaler.job')

# Initialiser FastAPI
app = FastAPI(
    title="Crypto Trading Bot",
    description="This is an API for tracking the latest Bitcoin prices in real time and predict the future price.",
    version="1.0.0"
)


@app.get("/")
async def root():
    return {"message": "Bienvenue sur l'API de prévision du cours du Bitcoin"}

class Input(BaseModel):
    """
    Classe pour la validation de l'entrée.
    data : liste des derniers prix de clôture du BTC
    """
    data: list[float]

def execute_query(query, host='timescaledb', port=5432, dbname='postgres', user='postgres', password='postgres'):
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

def get_avg_price_24h():
    """Récupère le prix moyen du cours de bitcoin au cours des 24 dernières heures.

    Returns:
        float: Le prix moyen du cours de bitcoin au cours des 24 dernières heures.
    """

    # Créer la requête SQL pour obtenir la dernière heure de la base de données
    query_latest_time = "SELECT MAX(close_time) AS latest_time FROM btcusdt;"

    # Exécuter la requête SQL et récupérer le résultat
    result_latest_time = execute_query(query_latest_time)

    # Obtenir la dernière heure de la base de données
    latest_time = result_latest_time['latest_time'][0]

    # Calculer le temps 24 heures avant la dernière heure
    time_24h_ago = latest_time - timedelta(hours=24)

    # Créer la requête SQL pour obtenir la moyenne du prix du cours au cours des 24 dernières heures
    query_avg_price = f"""
        SELECT AVG(close) AS avg_close
        FROM btcusdt
        WHERE close_time BETWEEN '{time_24h_ago}' AND '{latest_time}';
    """

    # Exécuter la requête SQL et récupérer le résultat
    result_avg_price = execute_query(query_avg_price)

    # Retourner le prix moyen
    return result_avg_price['avg_close'][0]

@app.get("/ohlcv")
def get_ohlcv(nb_days: int = None):
    """
    Récupère toutes les valeurs OHLCV à partir de la base de données TimescaleDB.

    Args:
        nb_days (int, optional): Le nombre de jours à récupérer. 
                                 Si non défini, toutes les données sont récupérées.

    Returns:
        dict: Un dictionnaire contenant toutes les données OHLCV disponibles.
    """

    # Récupérer toutes les valeurs OHLCV depuis la base de données TimescaleDB
    if nb_days is not None:
        query = f"""
        SELECT 
            time_bucket('1 day', open_time) AS day,
            first(open, open_time) AS open,
            max(high) AS high,
            min(low) AS low,
            last(close, close_time) AS close,
            sum(volume) as volume
        FROM 
            btcusdt
        GROUP BY 
            day
        ORDER BY 
            day DESC
        LIMIT {nb_days};
        """
    else:
        query = f"""
        SELECT 
            time_bucket('1 day', open_time) AS day,
            first(open, open_time) AS open,
            max(high) AS high,
            min(low) AS low,
            last(close, close_time) AS close,
            sum(volume) as volume
        FROM 
            btcusdt
        GROUP BY 
            day
        ORDER BY 
            day DESC;
        """

    result = execute_query(query)

    return result.to_dict(orient='records')

@app.get("/prices")
def get_prices(nb_day: int):
    """
    Récupère les dernières valeurs du close price à partir de la base de données TimescaleDB.

    Args:
    count (int): Le nombre de valeurs à récupérer.

    Returns:
    dict: Un dictionnaire avec la clé "prices" et la liste des prix de clôture comme valeur.
    """

    # Récupérer les dernières valeurs du close price depuis la base de données TimescaleDB
    # query = f"SELECT close FROM btcusdt ORDER BY close_time DESC LIMIT {nb_day}"
    query = f"""
            SELECT time_bucket('1440 minutes', close_time) AS day, AVG(close) AS average_close
            FROM btcusdt
            GROUP BY day
            ORDER BY day DESC
            LIMIT {nb_day}
            """
    result = execute_query(query)
    print(result)

    return {'prices': result['average_close'].values.tolist()}


@app.post("/predict")
def predict(input: Input):
    """
    Prévoit le prochain prix du BTC en utilisant un modèle LSTM.

    Args:
    input (Input): L'entrée validée doit être une instance de la classe Input.

    Returns:
    dict: Un dictionnaire avec la clé "prediction" et la prédiction comme valeur.
    """
    # Convertir les données en DataFrame
    data = pd.DataFrame(input.data).values.reshape(-1, 1).astype('float32')

    # Normaliser les données
    data_scaled = scaler.transform(data)

    # Vérifier si les données ont la bonne forme
    if data_scaled.shape[0] != 3:
        raise HTTPException(status_code=400, detail="Input data should have three elements.")

    data_scaled_reshaped = data_scaled.reshape((1, 3, 1))

    # Prédiction
    prediction = model.predict(data_scaled_reshaped)
    prediction = scaler.inverse_transform(prediction)

    return {'prediction': prediction.tolist()[0][0]}


@app.get("/avg_price_24h")
def avg_price_24h():
    """Route pour obtenir le prix moyen du cours de bitcoin au cours des 24 dernières heures.

    Returns:
        dict: Un dictionnaire avec la clé 'avg_price_24h' et le prix moyen comme valeur.
    """
    avg_price = get_avg_price_24h()
    return {"avg_price_24h": avg_price}

@app.get("/latest_price")
async def latest_price():
    """
    Récupère le dernier prix du BTC à partir de la base de données TimescaleDB.

    Returns:
    dict: Un dictionnaire avec la clé "latest_price" et le dernier prix comme valeur.
    """

    # Récupérer le dernier prix du BTC depuis la base de données TimescaleDB
    query = "SELECT close FROM btcusdt ORDER BY close_time DESC LIMIT 1"

    # Exécuter la requête SQL et récupérer le résultat
    result = execute_query(query)

    # Vérifier si des données ont été retournées
    if result.empty:
        raise HTTPException(status_code=404, detail="No price data found.")

    # Récupérer le dernier prix
    latest_price = result['close'][0]

    return {"latest_price": latest_price}
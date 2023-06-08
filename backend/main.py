from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from tensorflow import keras
import psycopg2 as pg
import pandas as pd
import joblib

# Charger le modèle de prédiction et le scaler
model = keras.models.load_model('lstm.h5')
scaler = joblib.load('scaler.job')

# Initialiser FastAPI
app = FastAPI()

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
    query = f"SELECT close FROM btcusdt ORDER BY close_time DESC LIMIT {nb_day}"
    result = execute_query(query)

    return {'prices': result['close'].values.tolist()}



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

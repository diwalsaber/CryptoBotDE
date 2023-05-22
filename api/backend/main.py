from fastapi import FastAPI, Header
import joblib
from tensorflow.keras.models import load_model
from pydantic import BaseModel
from typing import Optional, List
import numpy as np
import pandas as pd
import psycopg2 as pg
from datetime import datetime, timedelta
from sklearn.metrics import mean_squared_error
from sklearn.model_selection import train_test_split
from tensorflow.keras.preprocessing.sequence import TimeseriesGenerator


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

def preprocess_data(data, feature_columns, target_column, test_size=0.2, batch_size=5, lookback=10, stride=1):
    """Preprocess the dataset for training and testing.
    
    Args:
        data (pandas.DataFrame): The dataset.
        feature_columns (list): The list of feature column names.
        target_column (str): The name of the target column.
        test_size (float, optional): The proportion of the dataset to include in the test split. Defaults to 0.2.
        batch_size (int, optional): The number of samples per gradient update. Defaults to 5.
        stride (int, optional): The period to apply between the timesteps in the output sequence. Defaults to 1.

        
    Returns:
        tuple: The preprocessed data as (X_train, X_test, y_train, y_test, target_scaler).
    """
    # Split the dataset into training and testing sets
    X = data[feature_columns].values.reshape(-1, 1).astype('float32')
    y = data[target_column].values.reshape(-1, 1).astype('float32')
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, shuffle=False)

    # Normalize the feature columns for the training and testing sets separately
    #scaler = MinMaxScaler()
    X_train = scaler.fit_transform(X_train)
    X_test = scaler.transform(X_test)

    # Normalize the target data for the training and testing sets separately
    y_train = scaler.fit_transform(y_train.reshape(-1, 1)).flatten()
    y_test = scaler.transform(y_test.reshape(-1, 1)).flatten()
    
    # Create TimeseriesGenerator for the training data
    train_generator = TimeseriesGenerator(X_train, y_train, length=lookback, batch_size=batch_size, stride=stride)
    
    # Create TimeseriesGenerator for the training data
    test_generator = TimeseriesGenerator(X_test, y_test, length=lookback, batch_size=batch_size, stride=stride)
    
    return X_train, X_test, y_train, y_test, train_generator, test_generator, scaler

def evaluate_model(y_test, y_test_pred, lookback=10):
    """Evaluate the LSTM model on the test set.
    Args:
        model (tf.keras.Model): The LSTM model.
        X_test (numpy.ndarray): The test features.
        y_test (numpy.ndarray): The test target.
        sequence_length (int, optional): The length of the input sequences. Defaults to 60.
    Returns:
        float: The Root Mean Squared Error of the model on the test set.
    """
    return np.sqrt(mean_squared_error(y_test[: - lookback], y_test_pred))



scaler = joblib.load('scaler.job')
model = load_model('lstm_day3.h5')
day = 3

sql_query = """
    SELECT time_bucket('1 day', opentime) AS open_time,
           last(closeprice, closetime) AS close_price
    FROM candlestickhistorical
    GROUP BY open_time
    ORDER BY open_time;
"""

df = load_data_from_Postgres(sql_query)


class Input(BaseModel):
    data: List[float]

api = FastAPI(
    title="API CryptoBot",
    description="API CryptoBot powered by FastAPI.",
    version="1.0.0")


@api.post('/predict2', name='Get the prediction with entering 3 last values')
def post_predict2(input: Input):
    prediction = ""
    sequence = pd.DataFrame(input.data).values.reshape(-1, 1).astype('float32')

    if len(input.data) == day:
        sequence_scaled = scaler.transform(sequence)
        sequence_scaled_reshaped = sequence_scaled.reshape(1, day, 1)
        prediction = model.predict(sequence_scaled_reshaped)
        prediction = scaler.inverse_transform(prediction)
        prediction = prediction.flatten()[0]
    
    return {
        'Sequence':str(sequence.flatten().tolist()),
        'Prediction':str(prediction) 
    }

@api.get('/predict', name='Get the prediction with the last values on database')
def get_predict():
    date_sequence = df['open_time'].iloc[-day:].values.tolist()
    date_sequence = [datetime.utcfromtimestamp(x/1000000000).strftime('%Y-%m-%d') for x in date_sequence]
    
    date_prediction = datetime.strptime(date_sequence[-1], "%Y-%m-%d")
    date_prediction = date_prediction + timedelta(days=1)
    date_prediction = date_prediction.strftime('%Y-%m-%d')
    
    sequence = df['close_price'].iloc[-day:].values.reshape(-1,1)
    sequence_scaled = scaler.transform(sequence)
    sequence_scaled_reshaped = sequence_scaled.reshape(1,day,1)
    prediction = model.predict(sequence_scaled_reshaped)
    prediction = scaler.inverse_transform(prediction)
    prediction = prediction.flatten()[0]
    
    return {
        'Date Sequence':str(date_sequence),    
        'Sequence':str(sequence.flatten().tolist()),
        'Date Prediction':str(date_prediction),
        'Prediction':str(prediction)
    }

@api.get('/score', name='Get the RMSE score of the model')
def get_score():
    X_train, X_test, y_train, y_test, train_generator, test_generator, scaler = preprocess_data(df, 'close_price', 'close_price', lookback=day, test_size=0.2, batch_size=1)
    
    # Get the model predictions
    y_test_pred = model.predict(test_generator)
    
    # Scale the data
    y_test_pred_rescaled = scaler.inverse_transform(y_test_pred)
    y_test_rescaled      = scaler.inverse_transform(y_test.reshape(-1, 1))
    rmse = evaluate_model(y_test_rescaled, y_test_pred_rescaled, lookback=day)
    
    return {
        'RMSE score on test data': str(rmse)
    }

@api.get('/model_summary', name='Get the model summary')
def get_model():
    #stringlist = []
    #model.summary(print_fn=lambda x: stringlist.append(x))
    #summary = "\n".join(stringlist)
    summary = []

    for layer in model.layers: summary.append(layer.get_config())
    
    return {
        'model layers': summary,
        'lookback day': day
    }


@api.post("/predict", name='Get the prediction with entering a list of values')
def post_predict(input: Input):
    # Convertir les données en DataFrame
    data = pd.DataFrame(input.data).values.reshape(-1, 1).astype('float32')

    # Normaliser les données
    data_scaled = scaler.transform(data)

    prediction_list = []

    # prediction on a list of 3 values at least
    if len(data) >= day:
         # the last sequence is not included    
        if len(data) > day:
            generator = TimeseriesGenerator(data_scaled, data_scaled, length=day, batch_size=1, stride=1)
            prediction = model.predict(generator)
            prediction = scaler.inverse_transform(prediction)
            prediction_list = prediction.flatten().tolist()

        # for the last sequence
        data_scaled_reshaped = data_scaled[-day:].reshape(1, day, 1)
        prediction = model.predict(data_scaled_reshaped)
        prediction = scaler.inverse_transform(prediction)
        prediction_list.append(prediction.flatten()[0])

    return {
            'prediction': str(prediction_list)
    }

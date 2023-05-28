from fastapi import FastAPI, Header, HTTPException
import joblib
from tensorflow.keras.models import load_model
from pydantic import BaseModel
from typing import Optional, List
import asyncio
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

# Fonction pour mettre à jour le dataframe pour les affichages
def update_dataframe(interval = "1 day", mov_avg = 30):
    """Retrieve a new dataframe according to the interval and compute moving average (new SQL request)

    Args:
        interval: the interval between 2 records (x days, x weeks, x months)
        mov_avg: value used to compute the moving average on the data close_price

    Returns:
        dataframe: new dataframe according to the interval and compute moving average
    """
    sql_query = " \
      SELECT a.*, AVG(close_price) OVER(ORDER BY open_time ROWS BETWEEN {} PRECEDING AND CURRENT ROW) AS moving_average \
      FROM \
        (SELECT time_bucket('{}', opentime) AS open_time, \
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
    ".format(mov_avg-1, interval)
    df = load_data_from_Postgres(sql_query)

    return df

def predict(input_data: List[float], nb_future = 1, input_last_date = "", last_values = True):
    """Predict the next values in the future

    Args:
        input_data: the list of values used for the prediction
        nb_future: number of next interval predictions
        last_values: True means prediction done on the last values of the list
                     False means prediction done on the entire list

    Returns:
        a list of predictions
    """
    # Convertir les donnes en dataframe
    data = pd.DataFrame(input_data).values.reshape(-1, 1).astype('float32')

    # Normaliser les données
    data_scaled = scaler.transform(data)

    # liste pour les predictions
    prediction_list = []

    # liste date pour predictions
    date_prediction_list = []
    if input_last_date != "":
        date_prediction = input_last_date
        # date prediction pour les precedentes sequences n'incluant pas la dernière séquence
        if (len(data) > day) and (last_values == False):
            date_prediction = datetime.strptime(date_prediction, "%Y-%m-%d")
            date_prediction = date_prediction - timedelta(days=len(data)-day)
            date_prediction = date_prediction.strftime('%Y-%m-%d')
            for i in range(len(data)-day):
                date_prediction = datetime.strptime(date_prediction, "%Y-%m-%d")
                date_prediction = date_prediction + timedelta(days=1)
                date_prediction = date_prediction.strftime('%Y-%m-%d')
                date_prediction_list.append(date_prediction)
        # date prediction pour la dernière sequence dans le futur
        for i in range(nb_future):
            date_prediction = datetime.strptime(date_prediction, "%Y-%m-%d")
            date_prediction = date_prediction + timedelta(days=1)
            date_prediction = date_prediction.strftime('%Y-%m-%d')
            date_prediction_list.append(date_prediction)

    # On fait la prediction si la liste contient au moins le nombre de loopbak pour les données
    if len(data) >= day:
        # Prediction pour les sequences n'incluant pas la dernière séquence
        if (len(data) > day) and (last_values == False):
            generator = TimeseriesGenerator(data_scaled, data_scaled, length=day, batch_size=1, stride=1)
            prediction = model.predict(generator)
            prediction = scaler.inverse_transform(prediction)
            prediction_list = prediction.flatten().tolist()

        # Prédiction pour la derniere sequence avec boucle pour la prediction dans le future 
        # Prediction de type 'Recursive Multi-step Forecast' (utilisation des dernières predictions pour la prochaine prediction)
        while nb_future >=1 :

            # Récupération de la dernière sequence (comprenant les dernières prédictions)
            data_scaled = data_scaled[-day:]
            # Pour info pour ne pas afficher des valeurs normalisées
            #data_unscaled = scaler.inverse_transform(data_scaled)
            #print("\nSequence: \n", data_unscaled)
            data_scaled_reshaped = data_scaled.reshape(1, day, 1)

            prediction = model.predict(data_scaled_reshaped)
            prediction_unscaled = scaler.inverse_transform(prediction)
            # Convertir le type numpy.float32 en type native python float
            prediction_unscaled = prediction_unscaled.flatten()[0].item()
            prediction_list.append(prediction_unscaled)
            #print("Prediction: ", prediction_unscaled)

            # Transforme data de type np.array en type list afin de rajouter la dernière prediction
            data_scaled = data_scaled.flatten().tolist()
            # data contient les données normalisées
            prediction = prediction.flatten()[0].item()
            data_scaled.append(prediction)
            # Transforme la liste en np.array (array de 1 colonne), format utiliser pour la prédiction
            data_scaled = np.array(data_scaled, dtype=float).reshape(-1,1)
      
            nb_future -= 1

    return prediction_list, date_prediction_list



scaler = joblib.load('scaler.job')
#model = load_model('lstm_day3.h5')
#day = 3
model = load_model('lstm_day9.h5')
day = 9

#sql_query = """
#    SELECT time_bucket('1 day', opentime) AS open_time,
#           last(closeprice, closetime) AS close_price,
#           first(openprice, opentime) AS open_price,
#           max(highprice) AS high_price,
#           min(lowprice) AS low_price,
#           sum(basevolume) AS volume,
#           max(closetime) AS close_time
#    FROM candlestickhistorical
#    GROUP BY open_time
#    ORDER BY open_time;
#"""

interval = "1 day"
mov_avg = 30
sql_query = " \
    SELECT a.*, AVG(close_price) OVER(ORDER BY open_time ROWS BETWEEN {} PRECEDING AND CURRENT ROW) AS moving_average \
    FROM \
        (SELECT time_bucket('{}', opentime) AS open_time, \
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
    ".format(mov_avg-1, interval)

df = load_data_from_Postgres(sql_query)


class Input(BaseModel):
    """a list of float values used for the prediction
    """
    data: List[float]
    date: Optional[str] = ""

api = FastAPI(
    title="API CryptoBot",
    description="API CryptoBot powered by FastAPI.",
    version="1.0.0")


@api.get('/', name='Check if the API is operational')
async def get_alive():
    """returns alive
    """
    return {
        'welcome': 'to CryptoBot API'
    }

@api.post('/predict2', name='Get the prediction with entering 3 values')
async def post_predict2(input: Input):
    """Get the prediction of BTC/USDT according to 3 values in the list
    """
    prediction = ""
    sequence = pd.DataFrame(input.data).values.reshape(-1, 1).astype('float32')

    if len(input.data) == day:
        sequence_scaled = scaler.transform(sequence)
        sequence_scaled_reshaped = sequence_scaled.reshape(1, day, 1)
        prediction = model.predict(sequence_scaled_reshaped)
        prediction = scaler.inverse_transform(prediction)
        # convert numpy.float32 to native python float
        prediction = prediction.flatten()[0].item()
    else:
        raise HTTPException(
            status_code=400,
            detail='List size incorrect'
        )
    
    return {
        'Sequence': sequence.flatten().tolist(),
        'Prediction': prediction 
    }

@api.get('/predict', name='Get the prediction with the last values on the database')
async def get_predict():
    """Get the prediction for the next day for BTC/USDT with the last three values on the database
    """
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
    # convert numpy.float32 to native python float
    prediction = prediction.flatten()[0].item()

    
    return {
        'date_sequence': date_sequence,
        'sequence': sequence.flatten().tolist(),
        'date_prediction': date_prediction,
        'prediction': prediction
    }

@api.get('/values', name='Get the last sequence values on the database')
async def get_values():
    """Get the the last sequence values on the database for BTC/USDT used for the prediction, the number of values in the list depends on the model
    """
    date_sequence = df['open_time'].iloc[-day:].values.tolist()
    date_sequence = [datetime.utcfromtimestamp(x/1000000000).strftime('%Y-%m-%d') for x in date_sequence]

    sequence = df['close_price'].iloc[-day:].values.reshape(-1,1)

    return {
        'close_time': date_sequence,
        'close_price': sequence.flatten().tolist(),
    }

@api.get('/data', name='Get the data on the database')
async def get_data(nb_records: Optional[int]=day, interval: Optional[str]="1 day", mov_avg: Optional[int]=30):
    """Get the data (open price, open time, close price, high price, close price, low price, volume) on the database for BTC/USDT
    """

    df = update_dataframe(interval, mov_avg)
    if nb_records > len(df):
        nb_records = len(df)


    open_time = df['open_time'].iloc[-nb_records:].values.reshape(-1,1)
    close_time = df['close_time'].iloc[-nb_records:].values.reshape(-1,1)
    close_price = df['close_price'].iloc[-nb_records:].values.reshape(-1,1)
    open_price = df['open_price'].iloc[-nb_records:].values.reshape(-1,1)
    high_price = df['high_price'].iloc[-nb_records:].values.reshape(-1,1)
    low_price = df['low_price'].iloc[-nb_records:].values.reshape(-1,1)
    base_volume = df['base_volume'].iloc[-nb_records:].values.reshape(-1,1)
    moving_average = df['moving_average'].iloc[-nb_records:].values.reshape(-1,1)

    return {
        'open_time': open_time.flatten().tolist(),
        'close_time': close_time.flatten().tolist(),
        'close_price': close_price.flatten().tolist(),
        'open_price': open_price.flatten().tolist(),
        'high_price': high_price.flatten().tolist(),
        'low_price': low_price.flatten().tolist(),
        'base_volume': base_volume.flatten().tolist(),
        'moving_average': moving_average.flatten().tolist()
    }

    
@api.get('/score', name='Get the RMSE score of the model')
async def get_score():
    """Get RMSE score for train and test data
    """
    # Compute test_size
    nb_records_X_train = 1673 # number of records used for the training of the model
    test_size = (len(df)-nb_records_X_train)/len(df)
    
    X_train, X_test, y_train, y_test, train_generator, test_generator, scaler = preprocess_data(df, 'close_price', 'close_price', lookback=day, test_size=test_size, batch_size=1)
    
    # Get the model predictions
    y_train_pred = model.predict(train_generator)
    y_test_pred = model.predict(test_generator)
    
    # Scale the data
    y_train_pred_rescaled = scaler.inverse_transform(y_train_pred)
    y_test_pred_rescaled = scaler.inverse_transform(y_test_pred)
    y_train_rescaled      = scaler.inverse_transform(y_train.reshape(-1, 1))
    y_test_rescaled      = scaler.inverse_transform(y_test.reshape(-1, 1))

    rmse_train = evaluate_model(y_train_rescaled, y_train_pred_rescaled, lookback=day)
    rmse_test = evaluate_model(y_test_rescaled, y_test_pred_rescaled, lookback=day)
    # convert numpy.float32 to native python float
    rmse_train = rmse_train.item()
    rmse_test = rmse_test.item()

    
    return {
        'RMSE_score_train_data': rmse_train,
        'RMSE_score_test_data': rmse_test
    }

@api.get('/model_summary', name='Get the model summary')
async def get_model():
    """Get information about the model (layers, lookback)
    """
    #stringlist = []
    #model.summary(print_fn=lambda x: stringlist.append(x))
    #summary = "\n".join(stringlist)
    summary = []

    for layer in model.layers: summary.append(layer.get_config())
    
    return {
        'model_layers': summary,
        'lookback_day': day
    }


@api.post("/predict", name='Get the prediction with entering a list of values')
async def post_predict(input: Input):
    """Get the prediction for BTC/USDT with a list of values
    """
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
        # convert numpy.float32 to native python float
        prediction_list.append(prediction.flatten()[0].item())
    else:
        raise HTTPException(
            status_code=400,
            detail='List size incorrect'
        )

    return {
            'prediction': prediction_list
    }

@api.post("/predict3", name='Get the predictions of the next days with entering a list of values')
async def post_predict3(input: Input, nb_future: Optional[int]=1, last_values: Optional[bool]=True):
    """Get the predictions of the next days for BTC/USDT with a list of values
    """
    prediction_list = []
    date_prediction_list = []

    # prediction on a list of x values at least (x=loopback, depending of the model used for the prediction)
    if len(input.data) >= day:
        prediction_list, date_prediction_list = predict(input.data, nb_future, input.date, last_values)
    else:
        raise HTTPException(
            status_code=400,
            detail='List size incorrect'
        )

    return {
            'date_prediction': date_prediction_list,
            'prediction': prediction_list
    }
    

import os

from fastapi import HTTPException, status
from keras import Sequential
from keras.callbacks import EarlyStopping
from keras.layers import LSTM, Dense, Dropout
from keras.preprocessing.sequence import TimeseriesGenerator
from typing import List
import numpy as np
import pandas as pd
from sklearn.metrics import mean_squared_error
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

import joblib
from keras.models import load_model

from cryptobot.common import DBUtils
from schemas import CreateModelInput
from cryptobot.common.cryptoutils import DBConnector, Singleton, Configuration

features_sql_functions = {
    'open_price': 'first(openprice, opentime) open_price',
    'high_price': 'max(highprice) high_price',
    'low_price': 'min(lowprice) low_price',
    'close_price': 'last(closeprice, closetime) close_price',
    'base_volume': 'sum(basevolume) base_volume',
    'close_time': 'max(closetime) close_time',
    'quote_volume': 'sum(quotevolume) quote_volume',
    'number_trades': 'sum(numbertrades) number_trades',
    'taker_buybase': 'sum(takerbuybase) taker_buybase',
    'taker_buyquote': 'sum(takerbuyquote) taker_buyquote',
}
def make_data_sql_query_from_cols(feature_columns:List[str], target:str=None, interval:str=None, asc:bool=True, limit:int=-1):
    #add features columns
    queryColumns = [features_sql_functions[col] for col in feature_columns]
    #add target column
    if target and (target not in feature_columns):
        queryColumns.append(features_sql_functions[target])
    sql_query = f"SELECT time_bucket('{interval}', opentime) AS open_time,"
    sql_query += ', '.join(queryColumns)
    sql_query += " FROM candlestickhistorical  GROUP BY open_time ORDER BY open_time"
    if not asc:
        sql_query += ' desc'
    if limit >= 0:
        sql_query += f" limit {limit} "
    return sql_query

def make_prediction_data_sql_query_from_cols(feature_columns:List[str], interval:str=None,limit:int=-1):
    return f"""SELECT {','.join(feature_columns)} FROM 
        ({make_data_sql_query_from_cols(feature_columns=feature_columns, interval=interval, limit=limit, asc=False)}) 
        as data order by open_time"""


def make_sql_query_from_input(create_model_input:CreateModelInput, asc:bool=True, limit:int=-1):
    return make_data_sql_query_from_cols(feature_columns=create_model_input.features, target=create_model_input.target,
                                         interval=create_model_input.interval, asc=asc, limit=limit)

def load_data_from_Postgres(query):
    """Load the dataset from a PostgreSQL TimescaleDB table using a SQL query.

    Args:
        query (str): The SQL query to load the data.

    Returns:
        pandas.DataFrame: The loaded dataset from Timescale DB as a pandas DataFrame.
    """
    try:
        conn = DBConnector.get_data_db_connection()
        data = pd.read_sql_query(query, conn)
        return data
    finally:
        DBConnector.return_data_db_connection(conn)

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
    if target_column not in feature_columns:
        data = data[[col.name for col in [target_column]+feature_columns]].astype(float)
    #scale data
    features_scaler = StandardScaler()
    target_scaler = StandardScaler()
    feats = features_scaler.fit_transform(data[[col.name for col in feature_columns]]).astype(float)
    target =target_scaler.fit_transform(data[[target_column.name]]).astype(float)

    X_train, X_test, y_train, y_test = train_test_split(feats, target, test_size=test_size, shuffle=False)
    # Create TimeseriesGenerator for the training data
    train_generator = TimeseriesGenerator(X_train, y_train, length=lookback, batch_size=batch_size, stride=stride)

    # Create TimeseriesGenerator for the training data
    test_generator = TimeseriesGenerator(X_test, y_test, length=lookback, batch_size=batch_size, stride=stride)

    return X_train, X_test, y_train, y_test, train_generator, test_generator, features_scaler, target_scaler

def create_model(create_model_input:CreateModelInput):
    df = load_data_from_Postgres(make_sql_query_from_input(create_model_input))

    model = create_lstm_model(create_model_input.lookback, len(create_model_input.features), create_model_input.units)
    X_train, X_test, y_train, y_test, train_generator, test_generator, features_scaler, target_scaler = preprocess_data(data=df, feature_columns=create_model_input.features,
                                                                                                target_column=create_model_input.target,
                                                                                                lookback=create_model_input.lookback,
                                                                                                batch_size=1, stride=1)

    # Train LSTM model
    #early_stopping = EarlyStopping(monitor='val_loss', mode='min', verbose=1)
    #trained_lstm_model, history = train_lstm_model_generator(model, train_generator, test_generator, epochs=create_model_input.epochs)
    trained_lstm_model = train_lstm_model(model, train_generator, epochs=create_model_input.epochs)
    # Get the model predictions for train and test sets
    pred_train = model.predict(train_generator)
    pred_test = model.predict(test_generator)

    # Scale the test/train data
    X_train_unscaled = features_scaler.inverse_transform(X_train)
    X_test_unscaled = features_scaler.inverse_transform(X_test)
    y_train_unscaled = target_scaler.inverse_transform(y_train)
    y_test_unscaled = target_scaler.inverse_transform(y_test)
    pred_train_unscaled = target_scaler.inverse_transform(pred_train)
    pred_test_unscaled = target_scaler.inverse_transform(pred_test)

    train_rmse_score = np.sqrt(mean_squared_error(y_train_unscaled[create_model_input.lookback:], pred_train_unscaled))
    score = {}
    score['rmse_train'] = train_rmse_score
    test_rmse_score = np.sqrt(mean_squared_error(y_test_unscaled[create_model_input.lookback:], pred_test_unscaled))
    score['rmse_test'] = test_rmse_score
    #train_mae_score = mean_absolute_error(y_train_unscaled[create_model_input.lookback:], pred_train_unscaled)
    #score['mae_train'] = train_mae_score
    #test_mae_score = mean_absolute_error(y_test_unscaled[create_model_input.lookback:], pred_test_unscaled)
    #score['mae_test'] = test_mae_score
    return add_model(create_model_input, model, features_scaler, target_scaler, score)

def create_lstm_model(lookback:int, num_features:int, units:int=50):
    """Create an LSTM model with the specified number of units.
    Args:
        input_shape (tuple): The shape of the input data.
        units (int, optional): The number of LSTM units. Defaults to 50.

    Returns:
        tf.keras.Model: The LSTM model.
    """
    model = Sequential()
    model.add(LSTM(units, activation='relu', return_sequences=True, input_shape=(lookback, num_features)))
    #model.add(Dropout(0.2))
    #model.add(LSTM(units, activation='relu', return_sequences=True, input_shape=(lookback, num_features)))
    #model.add(Dropout(0.2))
    model.add(LSTM(units, activation='relu', return_sequences=False))
    #model.add(Dropout(0.2))
    model.add(Dense(1))
    model.compile(optimizer='adam', loss='mse')
    return model

def create_lstm_model_2(lookback, num_features, loss='mean_squared_error', optimizer='adam', units=50):
    """Create an LSTM model with the specified number of units.
    Args:
        input_shape (tuple): The shape of the input data.
        units (int, optional): The number of LSTM units. Defaults to 50.

    Returns:
        tf.keras.Model: The LSTM model.
    """
    # Initialize the LSTM model
    model = Sequential()

    # Add LSTM layer
    model.add(LSTM(units=units, return_sequences=True, input_shape=(lookback,num_features)))
    model.add(Dropout(0.2))

    # Add another LSTM layer
    model.add(LSTM(units=units, return_sequences=True))
    model.add(Dropout(0.2))

    # Add Dense layer
    model.add(Dense(units=25))
    model.add(Dense(units=1))

    # Compile the model
    model.compile(optimizer=optimizer, loss=loss)

    return model

def train_lstm_model_generator(model, train_generator, test_generator, epochs=10):
    """Train the given LSTM model with the training data.

    Args:
        model (tensorflow.keras.models.Sequential): The LSTM model to be trained.
        X_train (numpy.ndarray): The training features.
        y_train (numpy.ndarray): The training target values.
        lookback (int, optional): The number of time steps to look back for generating the input sequences. Defaults to 10.
        epochs (int, optional): The number of epochs to train the model. Defaults to 50.
        batch_size (int, optional): The number of samples per gradient update. Defaults to 64.

    Returns:
        tensorflow.keras.models.Sequential: The trained LSTM model.
    """
    # Train the model
    #early_stopping = EarlyStopping(monitor='val_loss', patience=3, restore_best_weights=True)
    history = model.fit_generator(generator=train_generator, verbose=2, epochs=epochs, validation_data=test_generator)

    return model, history

def train_lstm_model(model, train_generator, epochs=10):
    """Train the given LSTM model with the training data.

    Args:
        model (tensorflow.keras.models.Sequential): The LSTM model to be trained.
        X_train (numpy.ndarray): The training features.
        y_train (numpy.ndarray): The training target values.
        lookback (int, optional): The number of time steps to look back for generating the input sequences. Defaults to 10.
        epochs (int, optional): The number of epochs to train the model. Defaults to 10.

        stride (int, optional): The period to apply between the timesteps in the output sequence. Defaults to 1.

    Returns:
        tensorflow.keras.models.Sequential: The trained LSTM model.
    """
    # Train the model
    early_stopping = EarlyStopping(monitor='loss', patience=10, restore_best_weights=True)
    model.fit(train_generator, epochs=epochs, callbacks=[early_stopping])

    return model

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



class Models(metaclass=Singleton):
    def __init__(self):
        self.configuration = Configuration.get_instance()
        self.models = []
        db_models = DBUtils.get_models(True)
        for db_model in db_models:
            if existsAndReadableFile(db_model['features_scaler_path']):
                if existsAndReadableFile(db_model['target_scaler_path']):
                    if existsAndReadableFile(db_model['model_path']):
                        try:
                            self.add_model(db_model['id'], db_model['symbol'], db_model['interval'],
                                           db_model['lookback'],
                                           load_model(db_model['model_path']),
                                           joblib.load(db_model['features_scaler_path'])
                                           , joblib.load(db_model['target_scaler_path']))
                        except Exception as e:
                            print(f"Cannot load model with id {db_model['id']}:", e)
                    else:
                        print(f"model [id={db_model['id']}] file missing or has no read right:{db_model['model_path']}")
                else:
                    print(f"model [id={db_model['id']}] target scaler file missing or has no read right:{db_model['target_scaler_path']}")
            else:
                print(f"model [id={db_model['id']}] features scaler file missing or has no read right:{db_model['features_scaler_path']}")


    @staticmethod
    def get_instance():
        return Models()

    def get_model_by_id(self, model_id: int):
        filtered = list(filter(lambda m: m['id'] == model_id, self.models))
        if len(filtered) > 0:
            return filtered[0]

    def add_model(self, id: int, symbol: str, interval: str, lookback: int, model, features_scaler, target_scaler):
        self.models.append({'id': id,
                            'symbol': f"{symbol}",
                            'interval': f"{interval}",
                            'lookback': lookback,
                            'model': model,
                            'features_scaler': features_scaler,
                            'target_scaler': target_scaler
                            })

    def get_model_by_symbol(self, symbol: str, interval: str):
        filtered = list(filter(lambda m: m['symbol'] == symbol and m['interval'] == interval, self.models))
        if len(filtered) > 0:
            return filtered[0]

def existsAndReadableFile(filename):
    os.path.isfile(filename) and os.access(filename, os.R_OK)
def add_model(create_model_input:CreateModelInput, model, features_scaler, target_scaler, score):
    try:
        connection = DBConnector.get_app_db_connection()
        cursor = connection.cursor()
        cursor.execute("select nextval( 'seq_models')")
        model_id = cursor.fetchone()[0]
        model_path = f'{create_model_input.dir}/model_{model_id}.h5'
        features_scaler_path = f'{create_model_input.dir}/features_scaler_{model_id}.job'
        target_scaler_path = f'{create_model_input.dir}/target_scaler_{model_id}.job'
        summary = []
        for layer in model.layers: summary.append(layer.get_config())

        cursor.execute(f"""insert into models values ({model_id},'{create_model_input.symbol}',
        '{create_model_input.interval}',
        '{','.join(create_model_input.features)}',
        '{create_model_input.target}',
        {create_model_input.lookback},
        {create_model_input.epochs},
        {create_model_input.units}, 
        '{model_path}','{features_scaler_path}','{target_scaler_path}', False,
        '{str(summary).replace("'","''")}',
        '{str(score).replace("'","''")}')""")
        # save scaler
        joblib.dump(features_scaler, features_scaler_path)
        joblib.dump(target_scaler, target_scaler_path)
        # save model
        model.save(model_path)
        Models.get_instance().add_model(model_id, create_model_input.symbol, create_model_input.interval,
                                        create_model_input.lookback, model, features_scaler, target_scaler)
        connection.commit()
        return model_id
    finally:
        DBConnector.return_app_db_connection(connection)


def load_prediction_data(model_id: int):
    try:
        model = DBUtils.get_model(model_id)
        if model:
            df =  load_data_from_Postgres(make_prediction_data_sql_query_from_cols(
                            feature_columns=model['features'].split(','), interval=model['interval'], limit=model['lookback']))
            return df
        else:
            raise HTTPException(
                status_code=status.HTTP_404_BAD_REQUEST,
                detail={'message': f'Model with ID {model_id} not found!'}
            )
    except Exception as e:
        print(e)



def get_moving_data(mov_avg:int, interval:str, nb_records:int):
    """Retrieve a new dataframe according to the interval and compute moving average (new SQL request)

        Args:
            interval: the interval between 2 records (x days, x weeks, x months)
            mov_avg: value used to compute the moving average on the data close_price

        Returns:
            dataframe: new dataframe according to the interval and compute moving average
        """
    sql_query = f""" 
          SELECT a.*, AVG(close_price) OVER(ORDER BY open_time ROWS BETWEEN {mov_avg - 1} PRECEDING AND CURRENT ROW) AS moving_average 
          FROM 
            (SELECT time_bucket('{interval}', opentime) AS open_time, 
                    first(openprice, opentime) AS open_price, 
                    max(highprice) AS high_price, 
                    min(lowprice) AS low_price, 
                    last(closeprice, closetime) AS close_price, 
                    sum(basevolume) AS base_volume, 
                    max(closetime) AS close_time 
            FROM candlestickhistorical 
            GROUP BY open_time 
            ORDER BY open_time
            ) AS a; """
    df = load_data_from_Postgres(sql_query)

    return df


def load_active_model(symbol: str, interval:str):
    try:
        connection = DBConnector.get_app_db_connection()
        cursor = connection.cursor()
        cursor.execute(f"select model_path, features_scaler_path, target_scaler_path from models where interval = '{interval}' and symbol = '{symbol}' and active == True")
        row = cursor.fetchone()
        if row:
            return load_model(row[0]), joblib.load(row[1]), joblib.load(row[2])
    finally:
        DBConnector.return_app_db_connection(connection)

import os
from datetime import datetime

from cryptobot.common.exceptions import ExistingUser, NotExistingUser
from cryptobot.common import cryptoutils
from cryptobot.common.cryptoutils import DBConnector
import joblib
from keras.models import load_model

def create_user(email: str, password: str):
    try:
        if not exists(email):
            connection = DBConnector.get_app_db_connection()
            cursor = connection.cursor()
            cursor.execute(f"insert into users values (nextval('seq_users'),lower('{email}'), '{password}', True)")
            connection.commit()
        else:
            raise ExistingUser()
    finally:
        DBConnector.return_app_db_connection(connection)


def delete_user(email: str):
    try:
        if exists(email):
            connection = DBConnector.get_app_db_connection()
            cursor = connection.cursor()
            cursor.execute(f"DELETE FROM users where email = lower('{email}')")
            connection.commit()
        else:
            raise NotExistingUser()
    finally:
        DBConnector.return_app_db_connection(connection)


def get_user(email: str):
    try:
        connection = DBConnector.get_app_db_connection()
        cursor = connection.cursor()
        cursor.execute(f"SELECT email,password  FROM users where email = lower('{email}')")
        record = cursor.fetchone()
        if record:
            return {'email': record[0], 'password': record[1]}
        else:
            raise NotExistingUser()
    finally:
        DBConnector.return_app_db_connection(connection)


def get_user_id(email: str):
    try:
        connection = DBConnector.get_app_db_connection()
        cursor = connection.cursor()
        cursor.execute(f"SELECT *  FROM users where email = lower('{email}')")
        record = cursor.fetchone()
        if record:
            return record[0]
        else:
            raise NotExistingUser()
    finally:
        DBConnector.return_app_db_connection(connection)


def exists(email):
    try:
        connection = DBConnector.get_app_db_connection()
        cursor = connection.cursor()
        cursor.execute(f"SELECT id  FROM USERS WHERE EMAIL = lower('{email}')")
        record = cursor.fetchone()
        return record != None
    finally:
        DBConnector.return_app_db_connection(connection)


def add_token(email: str, token: str, refresh_token: str):
    try:
        user_id = get_user_id(email)
        connection = DBConnector.get_app_db_connection()
        cursor = connection.cursor()
        cursor.execute(f"insert into tokens values (nextval('seq_tokens'),'{user_id}', '{token}','{refresh_token}')")
        connection.commit()
    finally:
        DBConnector.return_app_db_connection(connection)


def get_tokens(email: str):
    try:
        user_id = get_user_id(email)
        connection = DBConnector.get_app_db_connection()
        cursor = connection.cursor()
        cursor.execute(f"select * from tokens where user_id = {user_id}")
        rows = cursor.fetchall()
        if rows:
            return list(map(lambda x: {'access_token': f'{x[0]}', 'refresh_token': f'{x[1]}'}, rows))
    finally:
        DBConnector.return_app_db_connection(connection)


def delete_tokens(email: str):
    try:
        user_id = get_user_id(email)
        connection = DBConnector.get_app_db_connection()
        cursor = connection.cursor()
        cursor.execute(f"DELETE FROM tokens where user_id = {user_id}")
        connection.commit()
    finally:
        DBConnector.return_app_db_connection(connection)


def delete_token(email: str, token: str):
    try:
        user_id = get_user_id(email)
        connection = DBConnector.get_app_db_connection()
        cursor = connection.cursor()
        cursor.execute(f"DELETE FROM tokens where user_id = {user_id} and token='{token}'")
        connection.commit()
    finally:
        DBConnector.return_app_db_connection(connection)


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

def get_models(include_invalids:bool = False):
    try:
        connection = DBConnector.get_app_db_connection()
        cursor = connection.cursor()
        sql = f"select id, symbol,interval,lookback,model_path,features_scaler_path,target_scaler_path,activated,summary,scores,features,target,epochs, units from models"
        if not include_invalids:
            sql += " where activated = True"
        cursor.execute(sql)
        rows = cursor.fetchall()
        return [{'id':row[0],
                'symbol':f'{row[1]}',
                'interval':f'{row[2]}',
                'lookback':row[3],
                'model_path':f'{row[4]}',
                'features_scaler_path':f'{row[5]}',
                'target_scaler_path':f'{row[6]}',
                'activated':row[7],
                'summary': row[8],
                'scores': row[9],
                'features': row[10],
                'target': row[11],
                'epochs': row[12],
                'units': row[13]
             } for row in rows]
    finally:
        DBConnector.return_app_db_connection(connection)

def exists_model(model_id:int):
    try:
        connection = DBConnector.get_app_db_connection()
        cursor = connection.cursor()
        sql = f"select id from models where id = {model_id}"
        cursor.execute(sql)
        row = cursor.fetchone()
        if row:
            return True
        else:
            return False
    finally:
        DBConnector.return_app_db_connection(connection)
def get_model(model_id:int):
    try:
        connection = DBConnector.get_app_db_connection()
        cursor = connection.cursor()
        sql = f"select * from models where id = {model_id}"
        cursor.execute(sql)
        row = cursor.fetchone()
        if row:
            return {'id':row[0],
                    'symbol':f'{row[1]}',
                    'interval':f'{row[2]}',
                    'features':f'{row[3]}',
                    'target':f'{row[4]}',
                    'lookback':row[5],
                    'epochs':row[6],
                    'units':row[7],
                    'model_path':f'{row[8]}',
                    'features_scaler_path':f'{row[9]}',
                    'target_scaler_path':f'{row[10]}',
                    'activated':row[11],
                    'summary':f"{row[12]}",
                    'scores': f"{row[13]}"
                 }
    finally:
        DBConnector.return_app_db_connection(connection)

def delete_model_by_id(model_id:int):
    try:
        if exists_model(model_id):
            connection = DBConnector.get_app_db_connection()
            cursor = connection.cursor()
            #delete model from filesystem
            cursor.execute(
                f"sdelete from models where id = {model_id}")
            connection.commit()
            return True
    finally:
        DBConnector.return_app_db_connection(connection)
def delete_model(symbol: str, interval:str):
    try:
        connection = DBConnector.get_app_db_connection()
        cursor = connection.cursor()
        #delete model from filesystem
        cursor.execute(
            f"select model_path, features_scaler_path, target_scaler_path from models where interval = '{interval}' and symbol = '{symbol}' and active == True")
        row = cursor.fetchone()
        if row:
            os.remove(row[0])
            os.remove(row[1])
            os.remove(row[2])
        cursor.execute(f"DELETE FROM models where symbol = '{symbol}' and interval ='{interval}'")
        connection.commit()
    finally:
        DBConnector.return_app_db_connection(connection)


def activate_model(model_id:int):
    try:
        connection = DBConnector.get_app_db_connection()
        cursor = connection.cursor()
        #deactivate others
        cursor.execute(f"""update models set activated = False 
            where symbol = (select symbol from models where id = {model_id})  and interval = (select interval from models where id = {model_id})""")
        #activate model by id
        cursor.execute(f"update models set activated = True where id = {model_id}")
        connection.commit()
        return get_model(model_id)
    finally:
        DBConnector.return_app_db_connection(connection)

def deactivate_model(model_id:int):
    try:
        connection = DBConnector.get_app_db_connection()
        cursor = connection.cursor()
        #deactivate model by id
        cursor.execute(f"update models set activated = False where id = {model_id}")
        connection.commit()
        return get_model(model_id)
    finally:
        DBConnector.return_app_db_connection(connection)


def delete_history_config(symbol:str, interval:str):
    try:
        symbol_id = cryptoutils.get_symbol_id(symbol)
        connection = DBConnector.get_data_db_connection()
        cursor = connection.cursor()
        cursor.execute(f"""DELETE FROM historydataconfig where  symbolid = {symbol_id} and interval = '{interval}')""")
        connection.commit()
    finally:
        DBConnector.return_data_db_connection(connection)
def add_history_config(symbol:str, interval:str, startdate:datetime, dir:str):
    try:
        connection = DBConnector.get_data_db_connection()
        cursor = connection.cursor()
        cursor.execute(f"""INSERT INTO SYMBOL SELECT nextval('seq_symbol'), '{symbol}','' WHERE NOT EXISTS (SELECT SymbolId FROM SYMBOL WHERE name = '{symbol}')""")
        connection.commit()
        symbol_id = cryptoutils.get_symbol_id(symbol)
        print(symbol_id)
        cursor.execute(f"""INSERT into historydataconfig values (nextval('SEQ_hist_config'), {symbol_id}, '{interval}', '{dir}','{startdate.strftime('%Y-%m-%dT%H:%M:%SZ')}')
        ON CONFLICT(symbolid, interval) DO UPDATE SET dir = '{dir}', startdate='{startdate.strftime('%Y-%m-%dT%H:%M:%SZ')}'""")
        connection.commit()
    finally:
        DBConnector.return_data_db_connection(connection)


def get_history_config(config_id:int):
    try:
        connection = DBConnector.get_data_db_connection()
        cursor = connection.cursor()
        cursor.execute(f"""select h.id, s.name, h.interval,h.dir,h.startdate from historydataconfig h 
        left join symbol s on s.symbolid = h.symbolid where h.id = {config_id}""")
        row = cursor.fetchone()
        if row:
            return {'id':row[0],'symbol':f"{row[1]}",'interval':f"{row[2]}", 'dir':f"{row[3]}",'startdate':row[4]}

    finally:
        DBConnector.return_data_db_connection(connection)

def is_loaded_csv(filename):
    try:
        connection = DBConnector.get_data_db_connection()
        cursor = connection.cursor()
        cursor.execute(f"""select * from loaded_csv where filename = '{filename}'""")
        row = cursor.fetchone()
        if row:
            return True
        else:
            return False
    finally:
        DBConnector.return_data_db_connection(connection)



def add_loaded_csv(filename):
    try:
        connection = DBConnector.get_data_db_connection()
        cursor = connection.cursor()
        cursor.execute(f"""insert into loaded_csv values('{filename}')""")
        connection.commit()
    finally:
        DBConnector.return_data_db_connection(connection)
def get_history_configs():
    try:
        connection = DBConnector.get_data_db_connection()
        cursor = connection.cursor()
        cursor.execute("""select h.id, s.name, h.interval,h.dir,h.startdate  from historydataconfig h left join symbol s on s.symbolId = h.symbolid""")
        rows = cursor.fetchall()
        return [{'id':row[0],'symbol':f"{row[1]}",'interval':f"{row[2]}", 'dir':f"{row[3]}",'startdate':row[4]} for row in rows]
    finally:
        DBConnector.return_data_db_connection(connection)


def get_min_start_date(symbolid:int):
    try:
        connection = DBConnector.get_data_db_connection()
        cursor = connection.cursor()
        cursor.execute(f"""select min(opentime)   from candlestickhistorical where symbolid = {symbolid}""")
        row = cursor.fetchone()
        if row:
            return row[0]
        else:
            return None
    finally:
        DBConnector.return_data_db_connection(connection)

def get_max_start_date(symbolid:int, interval:str):
    try:
        connection = DBConnector.get_data_db_connection()
        cursor = connection.cursor()
        cursor.execute(f"""select min(opentime)   from candlestickhistorical where symbolid = {symbolid} and interval='{interval}'""")
        row = cursor.fetchone()
        if row:
            return row[0]
        else:
            return None
    finally:
        DBConnector.return_data_db_connection(connection)


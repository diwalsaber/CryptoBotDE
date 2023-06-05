import psycopg2

from cryptobot.common.cryptoutils import DBConnector, Configuration

def create_data_db_schema():
    connection = None
    try:
        connection = DBConnector.get_data_db_connection()
        print(connection)
        cursor = connection.cursor()

        #create Symbol table and its objects (sequence, index..)
        cursor.execute("""CREATE TABLE IF NOT EXISTS Symbol (
            SymbolId integer,
            Name varchar(50),
            Description varchar(50),
            PRIMARY KEY (SymbolId)
        );
        """)
        cursor.execute("CREATE SEQUENCE  IF NOT EXISTS SEQ_SYMBOL;")
        cursor.execute("CREATE INDEX  IF NOT EXISTS IDX_SYMBOL_NAME ON SYMBOL(NAME);")

        # create history data config
        cursor.execute("""CREATE TABLE IF NOT EXISTS historydataconfig (
                            id integer primary key,
                            symbolid integer,
                            interval varchar(10),
                            dir varchar(2000),
                            startdate timestamp, 
                            UNIQUE (symbolid, interval)
                        );
                        """)
        cursor.execute("CREATE SEQUENCE  IF NOT EXISTS SEQ_hist_config;")
        cursor.execute("""CREATE TABLE IF NOT EXISTS loaded_csv (
                                    filename varchar(2000)
                                );
                                """)
        #History data table and its objects
        cursor.execute("""
         CREATE TABLE  IF NOT EXISTS CandleStickHistorical (
            OpenTime TIMESTAMP WITHOUT TIME ZONE, 
            SymbolId integer NOT NULL,
            OpenPrice FLOAT,
            HighPrice FLOAT,
            LowPrice FLOAT,
            ClosePrice FLOAT,
            BaseVolume FLOAT,
            CloseTime TIMESTAMP WITHOUT TIME ZONE,
            QuoteVolume FLOAT,
            NumberTrades FLOAT,
            TakerBuyBase FLOAT,
            TakerBuyQuote FLOAT,
            PRIMARY KEY (OpenTime, SymbolId),
            FOREIGN KEY (SymbolId) REFERENCES Symbol(SymbolId)
        );
        """)
        cursor.execute("SELECT create_hypertable('CandleStickHistorical', 'opentime', if_not_exists => TRUE);")
        cursor.execute("CREATE INDEX  IF NOT EXISTS IDX_HIST_OPENTIME ON CandleStickHistorical(OPENTIME)")
        cursor.execute("CREATE INDEX  IF NOT EXISTS IDX_HIST_CLOSETIME ON CandleStickHistorical(CLOSETIME)")
        #real time data table and its objects
        cursor.execute("""
         CREATE TABLE  IF NOT EXISTS CandleStickRealTime (
            OpenTime TIMESTAMP WITHOUT TIME ZONE, 
            SymbolId integer NOT NULL,
            OpenPrice FLOAT,
            HighPrice FLOAT,
            LowPrice FLOAT,
            ClosePrice FLOAT,
            BaseVolume FLOAT,
            CloseTime TIMESTAMP WITHOUT TIME ZONE,
            QuoteVolume FLOAT,
            NumberTrades FLOAT,
            TakerBuyBase FLOAT,
            TakerBuyQuote FLOAT,
            PRIMARY KEY (OpenTime, SymbolId),
            FOREIGN KEY (SymbolId) REFERENCES Symbol(SymbolId)
        );
        """)
        cursor.execute("SELECT create_hypertable('CandleStickRealTime', 'opentime', if_not_exists => TRUE);")
        cursor.execute("CREATE INDEX  IF NOT EXISTS IDX_HIST_OPENTIME ON CandleStickRealTime(OPENTIME)")
        cursor.execute("CREATE INDEX  IF NOT EXISTS IDX_HIST_CLOSETIME ON CandleStickRealTime(CLOSETIME)")
        connection.commit()
    except (Exception, psycopg2.DatabaseError) as error:
        print('--------------1')
        print(error)
    finally:
        DBConnector.return_data_db_connection(connection)

def create_app_db_schema():
    connection = None
    try:
        connection = DBConnector.get_app_db_connection()
        cursor = connection.cursor()
        #users table
        cursor.execute("""CREATE TABLE IF NOT EXISTS users (
            id integer  PRIMARY KEY,
            email varchar(200),
            password varchar(200),
            active boolean default True)
            """)
        cursor.execute("CREATE SEQUENCE  IF NOT EXISTS SEQ_USERS;")
        cursor.execute("CREATE INDEX  IF NOT EXISTS IDX_USERS_EMAIL ON Users(email)")

        #tokens table
        cursor.execute("""CREATE TABLE IF NOT EXISTS tokens (
                    id integer primary key,
                    user_id integer,
                    token varchar(1000),
                    refresh_token varchar(1000),
                    CONSTRAINT fk_users FOREIGN KEY(user_id) REFERENCES users(id))
                    """)
        cursor.execute("CREATE SEQUENCE  IF NOT EXISTS SEQ_TOKENS;")
        cursor.execute("CREATE INDEX  IF NOT EXISTS IDX_TOKENS_USER_ID ON tokens(user_id)")

        #models table
        cursor.execute("""CREATE TABLE IF NOT EXISTS models (
                            id integer primary key,
                            symbol varchar(10),
                            interval varchar(10),
                            features varchar(2000),
                            target varchar(2000),
                            lookback integer,
                            epochs integer,
                            units integer,
                            model_path varchar(1000),
                            features_scaler_path varchar(1000),
                            target_scaler_path varchar(1000),
                            activated boolean default False,
                            summary text,
                            scores text)
                            """)
        cursor.execute("CREATE SEQUENCE  IF NOT EXISTS SEQ_MODELS;")
        connection.commit()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        DBConnector.return_app_db_connection(connection)
def exists(cur, symbol):
    query = "select * from Symbol where name ='{}'".format(symbol)
    cur.execute(query)
    mobile_records = cur.fetchall()
    return len(mobile_records)  > 0

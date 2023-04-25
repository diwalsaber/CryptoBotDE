import psycopg2
import datetime

conn = psycopg2.connect(
    host="localhost",
    port="5432",
    database="postgres",
    user="postgres",
    password="postgres"
)

cur = conn.cursor()

cur.execute("""
CREATE TABLE Symbol (
    SymbolId integer,
    Name varchar(50),
    Description varchar(50),
    PRIMARY KEY (SymbolId)
);
""")

cur.execute("""
CREATE TABLE CandleStickHistorical (
    OpenTime timestamp, 
    SymbolId integer NOT NULL,
    OpenPrice FLOAT,
    HighPrice FLOAT,
    LowPrice FLOAT,
    ClosePrice FLOAT,
    BaseVolume FLOAT,
    CloseTime timestamp,
    QuoteVolume FLOAT,
    NumberTrades FLOAT,
    TakerBuyBase FLOAT,
    TakerBuyQuote FLOAT,
    PRIMARY KEY (OpenTime, SymbolId),
    FOREIGN KEY (SymbolId) REFERENCES Symbol(SymbolId)
);
""")

cur.execute("""
CREATE TABLE CandleStickRealTime (
    OpenTime timestamp, 
    SymbolId integer NOT NULL,
    OpenPrice FLOAT,
    HighPrice FLOAT,
    LowPrice FLOAT,
    ClosePrice FLOAT,
    BaseVolume FLOAT,
    CloseTime timestamp,
    QuoteVolume FLOAT,
    NumberTrades FLOAT,
    TakerBuyBase FLOAT,
    TakerBuyQuote FLOAT,
    PRIMARY KEY (OpenTime, SymbolId),
    FOREIGN KEY (SymbolId) REFERENCES Symbol(SymbolId)
);
""")

cur.execute("""
SELECT create_hypertable('CandleStickHistorical', 'opentime');
""")

cur.execute("""
SELECT create_hypertable('CandleStickRealTime', 'opentime');
""")

conn.commit()
cur.close()
conn.close()

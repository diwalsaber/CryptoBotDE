
import psycopg2
import csv
import pandas as pd
import os
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
    SymbolId integer NOT NULL,
	Name text NOT NULL,
	Description text,
	PRIMARY KEY (SymbolId)
)
""")

cur.execute("""
CREATE TABLE CandlestickHistorical (
    open_time timestamp, 
    SymbolId integer NOT NULL,
	Interval text NOT NULL,
    open_price FLOAT,
    high_price FLOAT,
    low_price FLOAT,
    close_price FLOAT,
    base_volume FLOAT,
    close_time FLOAT,
    quote_volume FLOAT,
    number_trades FLOAT,
    taker_buy_base FLOAT,
    taker_buy_quote FLOAT,
    ignore INT,
    PRIMARY KEY (open_time, SymbolId, Interval),
    FOREIGN KEY (SymbolId) REFERENCES Symbol(SymbolId)
    );
""")

#Requêtes SQL pour remplir la table symbole
#open_time = 1645369200000

# Requêtes SQL pour remplir la table symbole
#dt = datetime.datetime.fromtimestamp(open_time / 1000.0)
values = [(1, "BTCUSDT", "BTC: Bitcoin, USDT: TetherUS"), 
          (2, "ETHUSDT", "ETH: Ethereum, USDT: TetherUS"),
          (3, "DOGEUSDT", "DOGE: Dogecoin, USDT: TetherUS")]

cur.executemany("INSERT INTO Symbol (SymbolId, Name, Description) VALUES (%s, %s, %s)", values)
directory = r'C:\Users\asnoun\Desktop\Projet_Crypto\historique_data'
symbol_dict = {"BTCUSDT": 1, "ETHUSDT": 2, "DOGEUSDT": 3}
 
#dt = datetime.datetime.fromtimestamp(open_time / 1000.0)
# Lire le répertoire et les fichiers CSV qu'il contient
for filename in os.listdir(directory):
    if filename.endswith(".csv"):
        filepath = os.path.join(directory, filename)
        # Extraire le nom du symbole et l'intervalle à partir du nom de fichier
        symbol, interval = filename.split('_')[:2]
        # Récupérer l'ID du symbole
        symbolId = symbol_dict[symbol]

        # Ouvrir le fichier CSV et créer un objet reader
        with open(filepath, 'r') as file:
            reader = csv.reader(file)
            # Skip the first row
            next(reader)

            # Insérer les données dans la table CandlestickHistorical
            for row in reader:
                timestamp = datetime.datetime.fromtimestamp(int(row[0]) / 1000.0)
                cur.execute("INSERT INTO CandlestickHistorical (open_time, SymbolId, Interval, open_price, high_price, low_price, close_price, base_volume, close_time, quote_volume, number_trades, taker_buy_base, taker_buy_quote, ignore) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", (timestamp, symbolId, interval, float(row[1]), float(row[2]), float(row[3]), float(row[4]), float(row[5]), float(row[6]), float(row[7]), float(row[8]), float(row[9]), float(row[10]), int(row[11])))
                
conn.commit()
cur.close()
conn.close()
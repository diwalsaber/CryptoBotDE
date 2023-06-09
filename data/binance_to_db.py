import datetime
import time
import psycopg2
from binance.client import Client

# Initialiser le client Binance
client = Client(api_key='your_api_key', api_secret='your_api_secret')

def run():
    def get_historical_data():
        # Initialiser le client Binance
        client = Client(api_key='your_api_key', api_secret='your_api_secret')

        # Convertir la date de début en millisecondes
        start_date = datetime.datetime(2023, 1, 6)
        start_date_ms = int(start_date.timestamp() * 1000)

        # Initialiser une liste vide pour contenir les klines
        klines = []

        # Obtenir les klines en boucle jusqu'à la date actuelle
        while True:
            # Obtenir les prochaines 1000 klines
            new_klines = client.get_historical_klines("BTCUSDT", Client.KLINE_INTERVAL_15MINUTE, start_date_ms, limit=1000)

            # Si aucune nouvelle kline n'a été retournée, c'est que nous avons atteint la fin
            if not new_klines:
                break

            # Ajouter les nouvelles klines à notre liste
            klines.extend(new_klines)

            # Mettre à jour la date de début pour la prochaine requête
            start_date_ms = new_klines[-1][0] + 1

            # Dormir 1 seconde entre les requêtes pour éviter de dépasser les limites de taux
            time.sleep(1)

        return klines

    def initialize_db():
        # Initialiser la connexion à la base de données
        conn = psycopg2.connect(
            host='timescaledb',
            port=5432,
            dbname='postgres',
            user='postgres',
            password='postgres'
        )
        cur = conn.cursor()

        # Créer une table si elle n'existe pas déjà
        cur.execute("""
            CREATE TABLE IF NOT EXISTS btcusdt (
                open_time TIMESTAMP NOT NULL,
                open DECIMAL NOT NULL,
                high DECIMAL NOT NULL,
                low DECIMAL NOT NULL,
                close DECIMAL NOT NULL,
                volume DECIMAL NOT NULL,
                close_time TIMESTAMP NOT NULL,
                quote_asset_volume DECIMAL NOT NULL,
                number_of_trades INTEGER NOT NULL,
                taker_buy_base_asset_volume DECIMAL NOT NULL,
                taker_buy_quote_asset_volume DECIMAL NOT NULL,
                PRIMARY KEY (open_time),
                ignore DECIMAL NOT NULL
            )
        """)
        
        # Commit les modifications et fermer la connexion
        conn.commit()
        cur.close()
        conn.close()

    def fill_db(klines):
        # Initialiser la connexion à la base de données
        conn = psycopg2.connect(
            host='timescaledb',
            port=5432,
            dbname='postgres',
            user='postgres',
            password='postgres'
        )
        cur = conn.cursor()

        # Insérer les données dans la base de données
        for kline in klines:
            cur.execute("""
                INSERT INTO btcusdt VALUES (
                    to_timestamp(%s / 1000), %s, %s, %s, %s, %s, to_timestamp(%s / 1000), %s, %s, %s, %s, %s
                )
            """, kline)

        # Commit les modifications et fermer la connexion
        conn.commit()
        cur.close()
        conn.close()

    # Collect data
    klines = get_historical_data()

    # Initialize the database
    initialize_db()

    # Fill the database with collected data
    fill_db(klines)
    
if __name__ == "__main__":
    run()
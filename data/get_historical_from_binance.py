import psycopg2
from binance.client import Client

# Initialiser le client Binance
client = Client(api_key='your_api_key', api_secret='your_api_secret')

def run():
    # Récupérer l'historique des données de la paire BTCUSDT
    klines = client.get_historical_klines("BTCUSDT", Client.KLINE_INTERVAL_1DAY, "17 Aug, 2017")

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
            ignore DECIMAL NOT NULL
        )
    """)

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
    
if __name__ == "__main__":
    run()
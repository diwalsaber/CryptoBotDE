import datetime
import time
import json
import os
from kafka import KafkaProducer
from binance.client import Client

# Configuration Kafka
KAFKA_BROKER_URL = os.getenv("KAFKA_BROKER_URL", "kafka:9092")
TOPIC_NAME = "binance_klines_raw"

# Clés API Binance (le producteur en aura besoin pour simuler le flux)
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY_PRODUCER",
                            "YOUR_PRODUCER_API_KEY")
BINANCE_API_SECRET = os.getenv("BINANCE_API_SECRET_PRODUCER",
                               "YOUR_PRODUCER_API_SECRET")


def get_sample_historical_data(limit_klines=100):
    """Récupère un petit échantillon de données historiques de Binance."""
    client = Client(api_key=BINANCE_API_KEY, api_secret=BINANCE_API_SECRET)
    # Récupérer des données récentes pour la simulation
    end_time = datetime.datetime.now()
    # Environ `limit_klines` de 15min
    start_time = end_time - datetime.timedelta(minutes=15 * limit_klines)

    start_date_ms = int(start_time.timestamp() * 1000)
    end_date_ms = int(end_time.timestamp() * 1000)

    print(f"Récupération de {limit_klines} klines depuis Binance...")
    klines = client.get_historical_klines(
        "BTCUSDT", Client.KLINE_INTERVAL_15MINUTE,
        # Binance API peut prendre str(timestamp_ms)
        start_str=str(start_date_ms),
        end_str=str(end_date_ms),
        limit=limit_klines
    )
    print(f"{len(klines)} klines récupérées.")
    return klines


def create_producer():
    """Crée et retourne un producteur Kafka."""
    retry_count = 0
    max_retries = 5
    while retry_count < max_retries:
        try:
            producer = KafkaProducer(
                bootstrap_servers=KAFKA_BROKER_URL,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                acks='all',  # Attendre la confirmation de tous les replicas
                retries=3,
                # Augmenter le timeout pour la connexion initiale
                connections_max_idle_ms=1000 * 60 * 5,  # 5 minutes
                request_timeout_ms=30000,  # 30 secondes
                retry_backoff_ms=1000  # 1 seconde entre les tentatives
            )
            print("Producteur Kafka connecté.")
            return producer
        except Exception as e:
            retry_count += 1
            error_msg = (
                f"Erreur de connexion du producteur Kafka "
                f"(tentative {retry_count}/{max_retries}): {e}"
            )
            print(error_msg)
            if retry_count >= max_retries:
                print("Nombre maximum de tentatives de connexion atteint.")
                return None
            time.sleep(5 * retry_count)  # Attente exponentielle simple
    return None


if __name__ == "__main__":
    print("Démarrage du producteur Kafka pour données historiques simulées...")

    num_klines_to_send = 50
    send_interval = 2

    # S'assurer que les clés API sont fournies
    if (BINANCE_API_KEY == "YOUR_PRODUCER_API_KEY" or
            BINANCE_API_SECRET == "YOUR_PRODUCER_API_SECRET"):
        error_message_keys = (
            "ERREUR: Veuillez définir les variables d'environnement "
            "BINANCE_API_KEY_PRODUCER et BINANCE_API_SECRET_PRODUCER."
        )
        print(error_message_keys)
        exit(1)

    klines_data = get_sample_historical_data(
        limit_klines=num_klines_to_send + 20
    )

    if not klines_data:
        print("Aucune donnée historique récupérée. Arrêt du producteur.")
        exit()

    producer = create_producer()

    if producer:
        try:
            count = 0
            for kline in klines_data:
                if count >= num_klines_to_send:
                    msg = f"Nombre maximum de {num_klines_to_send} messages envoyé."
                    print(msg)
                    break

                message = {
                    "open_time": kline[0],
                    "open": kline[1],
                    "high": kline[2],
                    "low": kline[3],
                    "close": kline[4],
                    "volume": kline[5],
                    "close_time": kline[6],
                    "quote_asset_volume": kline[7],
                    "number_of_trades": kline[8],
                    "taker_buy_base_asset_volume": kline[9],
                    "taker_buy_quote_asset_volume": kline[10],
                    "ignore": kline[11]
                }

                future = producer.send(TOPIC_NAME, value=message)
                # Attendre la confirmation de l'envoi (optionnel, debug)
                try:
                    record_metadata = future.get(timeout=10)
                    msg_sent = (
                        f"Message envoyé au topic {TOPIC_NAME}, "
                        f"partition {record_metadata.partition}, "
                        f"offset {record_metadata.offset}: O={message['open']}"
                    )
                    print(msg_sent)
                except Exception as e_send:
                    err_send_msg = (
                        f"Erreur lors de l'attente de la confirmation "
                        f"d'envoi: {e_send}"
                    )
                    print(err_send_msg)

                # producer.flush() # Peut ralentir, send est asynchrone
                count += 1
                time.sleep(send_interval)

        except Exception as e:
            print(f"Erreur lors de l'envoi de messages: {e}")
        finally:
            print("Fermeture du producteur Kafka.")
            producer.close()
    else:
        print("Impossible de créer le producteur Kafka. Arrêt.") 
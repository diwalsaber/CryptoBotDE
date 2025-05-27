import os
from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col
from pyspark.sql.types import (
    StructType, StructField, StringType, LongType, TimestampType, DoubleType
)

# Configuration TimescaleDB & Kafka
TIMESCALE_DB_USER = os.getenv("TIMESCALE_DB_USER", "postgres")
TIMESCALE_DB_PASSWORD = os.getenv("TIMESCALE_DB_PASSWORD", "postgres")
TIMESCALE_DB_HOST = os.getenv("TIMESCALE_DB_HOST", "timescaledb")
TIMESCALE_DB_PORT = os.getenv("TIMESCALE_DB_PORT", "5432")
TIMESCALE_DB_NAME = os.getenv("TIMESCALE_DB_NAME", "postgres")
TIMESCALE_TABLE_NAME = os.getenv("TIMESCALE_TABLE_NAME", "btcusdt")

KAFKA_BROKER_URL = os.getenv("KAFKA_BROKER_URL", "kafka:9092")
KAFKA_TOPIC = "binance_klines_raw"

# Assurez-vous que ce chemin est correct dans l'environnement Spark
JDBC_DRIVER_PATH = "/opt/bitnami/spark/jars/postgresql-42.7.3.jar"


def get_spark_session():
    """Crée et retourne une session Spark configurée."""
    spark = (SparkSession.builder
             .appName("KafkaToTimescaleStream")
             .config("spark.jars", JDBC_DRIVER_PATH)
             .config("spark.sql.session.timeZone", "UTC")
             .getOrCreate())
    print("SparkSession créée.")
    return spark


# Schéma des données klines attendues de Kafka (après désérialisation JSON)
# Doit correspondre à la structure du message produit
# par kafka_producer_historical.py
kline_schema = StructType([
    StructField("open_time", LongType(), True),      # Timestamp ms
    StructField("open", StringType(), True),
    StructField("high", StringType(), True),
    StructField("low", StringType(), True),
    StructField("close", StringType(), True),
    StructField("volume", StringType(), True),
    StructField("close_time", LongType(), True),     # Timestamp ms
    StructField("quote_asset_volume", StringType(), True),
    StructField("number_of_trades", LongType(), True),
    StructField("taker_buy_base_asset_volume", StringType(), True),
    StructField("taker_buy_quote_asset_volume", StringType(), True),
    StructField("ignore", StringType(), True)
])

# Schéma de la table TimescaleDB (btcusdt)
# open_time est TIMESTAMP WITHOUT TIME ZONE, correspond à TimestampType.
# Les champs numériques sont NUMERIC, convertis pour Spark.
# Notre table `btcusdt` a `open_time` comme clé primaire (TIMESTAMP)
timescale_schema_final = StructType([
    StructField("open_time", TimestampType(), nullable=False),  # Clé primaire
    StructField("open_price", DoubleType(), nullable=True),
    StructField("high_price", DoubleType(), nullable=True),
    StructField("low_price", DoubleType(), nullable=True),
    StructField("close_price", DoubleType(), nullable=True),
    StructField("volume", DoubleType(), nullable=True),
    StructField("close_time", TimestampType(), nullable=True),
    StructField("quote_asset_volume", DoubleType(), nullable=True),
    StructField("number_of_trades", LongType(), nullable=True),
    StructField("taker_buy_base_asset_volume", DoubleType(), nullable=True),
    StructField("taker_buy_quote_asset_volume", DoubleType(), nullable=True)
    # "ignore" n'est pas dans la table cible
])


def process_batch(batch_df, epoch_id):
    """
    Traite un micro-batch de données du stream Kafka et l'écrit dans TimescaleDB.
    """
    if batch_df.isEmpty():
        print(f"Epoch {epoch_id}: Pas de nouvelles données.")
        return

    print(f"Epoch {epoch_id}: Traitement de {batch_df.count()} lignes.")

    # Conversion et sélection des colonnes
    transformed_df = (batch_df
                      .withColumn("open_time_ts",
                                  (col("open_time") / 1000).cast(TimestampType()))
                      .withColumn("close_time_ts",
                                  (col("close_time") / 1000).cast(TimestampType()))
                      .select(
                          col("open_time_ts").alias("open_time"),
                          col("open").cast(DoubleType()).alias("open_price"),
                          col("high").cast(DoubleType()).alias("high_price"),
                          col("low").cast(DoubleType()).alias("low_price"),
                          col("close").cast(DoubleType()).alias("close_price"),
                          col("volume").cast(DoubleType()),
                          col("close_time_ts").alias("close_time"),
                          col("quote_asset_volume").cast(DoubleType()),
                          col("number_of_trades").cast(LongType()),
                          col("taker_buy_base_asset_volume").cast(DoubleType()),
                          col("taker_buy_quote_asset_volume").cast(DoubleType())
                      ))

    db_url = f"jdbc:postgresql://{TIMESCALE_DB_HOST}:{TIMESCALE_DB_PORT}/{TIMESCALE_DB_NAME}"
    properties = {
        "user": TIMESCALE_DB_USER,
        "password": TIMESCALE_DB_PASSWORD,
        "driver": "org.postgresql.Driver"
    }

    try:
        (transformed_df.write
         .jdbc(url=db_url,
               table=TIMESCALE_TABLE_NAME,
               mode="append",
               properties=properties))
        msg = f"Epoch {epoch_id}: Données écrites dans {TIMESCALE_TABLE_NAME}."
        print(msg)
    except Exception as e:
        print(f"Epoch {epoch_id}: Erreur écriture TimescaleDB: {e}")


def run_streaming_job():
    """Lance le job Spark Streaming."""
    spark = get_spark_session()

    raw_kafka_stream_df = (spark.readStream
                           .format("kafka")
                           .option("kafka.bootstrap.servers", KAFKA_BROKER_URL)
                           .option("subscribe", KAFKA_TOPIC)
                           .option("startingOffsets", "latest")
                           .load())

    print("Stream Kafka initialisé.")
    # raw_kafka_stream_df.printSchema() # Décommenter pour débogage

    json_expanded_df = (raw_kafka_stream_df
                        .select(from_json(col("value").cast("string"), kline_schema)
                                .alias("kline"))
                        .select("kline.*"))

    print("Schéma après expansion JSON:")
    # json_expanded_df.printSchema() # Décommenter pour débogage

    query = (json_expanded_df.writeStream
             .foreachBatch(process_batch)
             .outputMode("update")
             .trigger(processingTime='15 seconds')
             .start())

    msg_start = f"Job streaming démarré. Topic {KAFKA_TOPIC}..."
    print(msg_start)

    try:
        query.awaitTermination()
    except KeyboardInterrupt:
        print("Arrêt du stream initié par l'utilisateur...")
    finally:
        print("Arrêt du job de streaming.")
        spark.stop()


if __name__ == "__main__":
    print("Démarrage du job streaming Kafka vers TimescaleDB...")
    run_streaming_job() 
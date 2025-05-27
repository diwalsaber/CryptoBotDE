import datetime
import time
import psycopg2
from binance.client import Client
import pandas as pd
import os
from pyspark.sql import SparkSession
from pyspark.sql.types import (
    StructType, StructField, StringType, DecimalType, LongType, TimestampType,
    IntegerType
)
from pyspark.sql.functions import col
from datetime import timedelta

# Définir le répertoire de staging pour les fichiers Parquet
# Spark écrira dans un sous-répertoire ici,
# par exemple /app/parquet_data/spark_output/
PARQUET_STAGING_DIR = "parquet_data"
# Chemin où Spark s'attend à trouver les données (doit correspondre
# au volume mount dans docker-compose pour Spark)
SPARK_DATA_PATH = "/opt/bitnami/spark/data/"


def get_spark_session():
    """Initialise et retourne une SparkSession."""
    # Le driver JDBC pour PostgreSQL est nécessaire.
    # Vous pouvez le télécharger et le rendre disponible,
    # ou le spécifier dans spark-submit/spark-defaults.conf.
    # Pour l'image bitnami/spark, elle vient souvent avec des drivers
    # ou facilite leur ajout.
    # Cependant, pour la simplicité dans cet environnement
    # docker-compose bitnami, nous supposerons que le driver est accessible.
    spark = (SparkSession.builder
             .appName("BinanceDataProcessing")
             .master("local[*]")
             .config("spark.sql.legacy.parquet.datetimeRebaseModeInWrite",
                     "CORRECTED")
             .config("spark.sql.legacy.parquet.int96RebaseModeInWrite",
                     "CORRECTED")
             .config("spark.driver.extraClassPath",
                     "/opt/bitnami/spark/jars/postgresql-42.7.3.jar")
             .config("spark.executor.extraClassPath",
                     "/opt/bitnami/spark/jars/postgresql-42.7.3.jar")
             .getOrCreate())
    return spark


def get_last_open_time_from_db(spark, db_url, db_properties):
    """Récupère le dernier open_time de la table btcusdt."""
    try:
        # Vérifier si la table existe et n'est pas vide pour éviter une
        # erreur si on lit une table vide
        # Cela peut être fait de manière plus robuste,
        # mais pour l'instant, on essaie de lire.
        print("Tentative de lecture du dernier open_time depuis la base "
              "de données...")
        query = ("(SELECT MAX(open_time) as last_open_time FROM btcusdt) "
                 "as latest_data")
        df = spark.read.jdbc(url=db_url, table=query, properties=db_properties)
        last_open_time_row = df.first()
        if last_open_time_row and last_open_time_row["last_open_time"]:
            last_ts = last_open_time_row["last_open_time"]
            print(f"Dernier open_time trouvé dans la DB: {last_ts}")
            # Convertir en millisecondes
            return int(last_ts.timestamp() * 1000)
        else:
            print("Aucun open_time trouvé dans la DB "
                  "(table vide ou max est null).")
            return None
    except Exception as e:
        # Peut échouer si la table n'existe pas.
        # Dans ce cas, on considère comme un chargement initial.
        print(f"Erreur lors de la lecture du dernier open_time "
              f"(table peut ne pas exister): {e}")
        return None


def get_historical_data(start_after_timestamp_ms=None,
                        default_start_date_str="2023-01-01"):
    api_key_data = os.getenv('BINANCE_API_KEY', 'your_api_key')
    api_secret_data = os.getenv('BINANCE_API_SECRET', 'your_api_secret')
    client = Client(api_key=api_key_data, api_secret=api_secret_data)

    klines_list = []
    # Pour une exécution toutes les 15min, on s'attend à peu de klines.
    # Pour un rattrapage, la boucle continuera jusqu'à ce que les données
    # soient récentes ou que l'API ne retourne plus rien.
    # MAX_KLINES_CATCHUP n'est plus utilisé comme limite fixe de klines.

    # Limite le nombre d'appels API par exécution de cette fonction
    # pour segmenter les très longs backfills. Environ 50 appels 
    # * 1000 klines/appel * 15min/kline ~= 520 jours max par run.
    MAX_API_CALLS_PER_RUN = 50
    api_calls_count = 0

    if start_after_timestamp_ms:
        # On veut les klines *après* ce timestamp.
        # L'API Binance prend un start_str (timestamp en ms) qui est inclusif.
        # Donc, on doit prendre le timestamp de la bougie *suivante*.
        # Une bougie de 15min = 15 * 60 * 1000 ms = 900,000 ms
        # Début de la prochaine bougie
        start_date_ms = start_after_timestamp_ms + 900000  # 15 minutes après
        start_after_dt = datetime.datetime.fromtimestamp(
            start_after_timestamp_ms / 1000
        )
        current_start_dt = datetime.datetime.fromtimestamp(
            start_date_ms / 1000
        )
        print(
            f"Mise à jour incrémentale. Démarrage après: {start_after_dt}, "
            f"donc récupération à partir de {current_start_dt}"
        )
    else:
        # Chargement initial
        default_start_dt = datetime.datetime.strptime(
            default_start_date_str, "%Y-%m-%d"
        )
        start_date_ms = int(default_start_dt.timestamp() * 1000)
        print(f"Chargement initial. Démarrage à partir de: {default_start_dt}")

    processed_klines_count = 0
    while True:
        api_calls_count += 1
        if api_calls_count > MAX_API_CALLS_PER_RUN:
            print(
                f"Limite de {MAX_API_CALLS_PER_RUN} appels API atteinte "
                "pour cette exécution. Le backfill reprendra au "
                "prochain run."
            )
            break

        # L'API retourne au plus 1000 klines par appel.
        limit_per_call = 1000

        start_date_dt_readable = datetime.datetime.fromtimestamp(
            start_date_ms / 1000
        )
        print(
            f"Appel API Binance: start_time={start_date_dt_readable} "
            f"(ms={start_date_ms}), limit={limit_per_call}"
        )
        new_klines = client.get_historical_klines(
            "BTCUSDT", Client.KLINE_INTERVAL_15MINUTE,
            str(start_date_ms),  # Doit être une string
            limit=limit_per_call
        )

        if not new_klines:
            current_time_utc = datetime.datetime.now(datetime.timezone.utc)
            start_date_dt = datetime.datetime.fromtimestamp(
                start_date_ms / 1000, tz=datetime.timezone.utc
            )
            # Si la date de début demandée est encore loin dans le passé
            # (ex: plus de 24h) et qu'on ne reçoit rien, c'est suspect.
            if (current_time_utc - start_date_dt) > timedelta(days=1):
                print(
                    f"AVERTISSEMENT: Aucune nouvelle kline reçue pour "
                    f"start_time={start_date_dt}, alors que cette date est "
                    "encore dans le passé. Tentative d'avancer le "
                    "start_time pour le prochain appel."
                )
                # Avancer au prochain intervalle de 15min et continuer la 
                # boucle pour un autre appel API dans cette même exécution.
                start_date_ms += (15 * 60 * 1000)  # Avance de 15 min
                time.sleep(1)  # Petit délai avant de réessayer
                continue  # Tente le prochain appel API dans la boucle while
            else:
                print(
                    "Plus de nouvelles klines reçues de Binance pour cette "
                    "période (données récentes ou fin de l'historique)."
                )
                # Comportement normal: arrêt si données récentes ou fin 
                # d'historique
                break  

        klines_list.extend(new_klines)
        processed_klines_count += len(new_klines)
        print(
            f"Récupéré {len(new_klines)} klines dans cet appel. "
            f"Total klines_list: {len(klines_list)}. "
            f"Total traité: {processed_klines_count}"
        )

        # La condition MAX_KLINES_CATCHUP est retirée pour permettre un
        # backfill complet.
        # La boucle s'arrêtera si plus de nouvelles klines ou si les
        # données sont récentes.

        # Mettre à jour start_date_ms pour le prochain appel
        # pour obtenir le lot suivant
        # Début de la prochaine bougie de 15min
        start_date_ms = new_klines[-1][0] + (15 * 60 * 1000)

        # Si le dernier kline reçu est très récent
        # (ex: moins de 15-30min de maintenant), on peut arrêter.
        # Cela évite de boucler inutilement si on a tout rattrapé.
        last_kline_time = datetime.datetime.fromtimestamp(
            new_klines[-1][0] / 1000, tz=datetime.timezone.utc
        )
        if (datetime.datetime.now(datetime.timezone.utc) - last_kline_time
                < timedelta(minutes=30)):
            print("Les données collectées sont très récentes. "
                  "Arrêt de la collecte.")
            break

        time.sleep(0.5)

    print(f"Collecte terminée. {len(klines_list)} klines au total "
          "dans la liste.")
    return klines_list


def run(spark):
    # S'assurer que le répertoire de staging existe sur l'hôte,
    # Spark y écrira depuis le conteneur.
    # Le chemin à l'intérieur du conteneur Spark sera
    # SPARK_DATA_PATH + PARQUET_STAGING_DIR
    host_parquet_path = PARQUET_STAGING_DIR
    if not os.path.exists(host_parquet_path):
        os.makedirs(host_parquet_path, exist_ok=True)

    # Le chemin de sortie pour Spark à l'intérieur de son conteneur
    spark_output_parquet_dir = os.path.join(
        SPARK_DATA_PATH, PARQUET_STAGING_DIR, "spark_output"
    )

    # Configuration JDBC pour get_last_open_time_from_db
    # et fill_table_from_spark_parquet.
    db_url = "jdbc:postgresql://timescaledb:5432/postgres"
    db_properties = {
        "user": "postgres",
        "password": "postgres",
        "driver": "org.postgresql.Driver"
    }

    # Renommée pour clarifier
    def create_historic_table_if_not_exists():
        # Cette fonction utilise toujours psycopg2, car la création de table
        # est une op DDL simple. Spark est plus pour le DML à grande échelle.
        conn = None
        cur = None  # Initialiser cur en dehors du try pour le finally
        try:
            conn = psycopg2.connect(
                host='timescaledb', port=5432, dbname='postgres',
                user='postgres', password='postgres'
            )
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS btcusdt (
                    open_time TIMESTAMP NOT NULL PRIMARY KEY,
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
                    ignore_col DECIMAL NOT NULL
                )
            """)
            # Activation de l'hypertable TimescaleDB si ce n'est pas déjà fait
            # Note: create_hypertable ne doit être appelé qu'une seule fois.
            # Une vérification si la table est déjà une hypertable
            # serait plus robuste.
            cur.execute("""
                SELECT create_hypertable('btcusdt', 'open_time',
                                         if_not_exists => TRUE);
            """)
            conn.commit()
            print("Table 'btcusdt' vérifiée/créée "
                  "et configurée en hypertable.")
        except psycopg2.Error as e:
            print("Erreur lors de la création/configuration de la table: "
                  f"{e}")
        finally:
            if cur:
                cur.close()
            if conn:
                conn.close()

    def klines_to_spark_df_and_save_parquet(klines_list, output_path):
        columns = [
            'open_time_ms', 'open', 'high', 'low', 'close', 'volume',
            'close_time_ms', 'quote_asset_volume', 'number_of_trades',
            'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume',
            'ignore'
        ]

        # Schéma pour le DataFrame Spark, important pour la robustesse
        schema = StructType([
            StructField("open_time_ms", LongType(), True),
            StructField("open", StringType(), True),  # Lire comme String
            StructField("high", StringType(), True),
            StructField("low", StringType(), True),
            StructField("close", StringType(), True),
            StructField("volume", StringType(), True),
            StructField("close_time_ms", LongType(), True),
            StructField("quote_asset_volume", StringType(), True),
            StructField("number_of_trades", LongType(), True),
            StructField("taker_buy_base_asset_volume", StringType(), True),
            StructField("taker_buy_quote_asset_volume", StringType(), True),
            StructField("ignore", StringType(), True)
        ])

        # Créer un DataFrame Pandas d'abord pour la facilité
        # de manipulation initiale puis convertir en DataFrame Spark.
        # Cela pourrait être optimisé pour de très gros volumes
        # en créant directement un RDD.
        pd_df = pd.DataFrame(klines_list, columns=columns)

        # Convertir les millisecondes en secondes pour to_timestamp de Spark
        # si besoin, ou gérer la conversion.
        # Ici on les garde en ms et on les convertira pour l'insertion DB.
        spark_df = spark.createDataFrame(pd_df, schema=schema)

        # Conversion des types et renommage de colonnes
        # pour correspondre à la table SQL
        # Noter que 'open_time' et 'close_time' seront des Timestamps
        # Les autres colonnes DECIMAL et INTEGER
        spark_df = (spark_df.withColumn(
                        "open_time",
                        (col("open_time_ms") / 1000).cast(TimestampType()))
                    .withColumn(
                        "close_time",
                        (col("close_time_ms") / 1000).cast(TimestampType()))
                    .withColumn("open",
                                col("open").cast(DecimalType(18, 8)))
                    .withColumn("high",
                                col("high").cast(DecimalType(18, 8)))
                    .withColumn("low", col("low").cast(DecimalType(18, 8)))
                    .withColumn("close",
                                col("close").cast(DecimalType(18, 8)))
                    .withColumn("volume",
                                col("volume").cast(DecimalType(18, 8)))
                    .withColumn("quote_asset_volume",
                                col("quote_asset_volume")
                                .cast(DecimalType(18, 8)))
                    .withColumn("number_of_trades",
                                col("number_of_trades").cast(IntegerType()))
                    .withColumn("taker_buy_base_asset_volume",
                                col("taker_buy_base_asset_volume")
                                .cast(DecimalType(18, 8)))
                    .withColumn("taker_buy_quote_asset_volume",
                                col("taker_buy_quote_asset_volume")
                                .cast(DecimalType(18, 8)))
                    # Renommé pour correspondre à la table SQL
                    .withColumn("ignore_col",
                                col("ignore").cast(DecimalType(18, 8))))

        # Sélectionner et ordonner les colonnes
        # pour la sauvegarde et l'insertion
        final_df = spark_df.select(
            "open_time", "open", "high", "low", "close", "volume",
            "close_time", "quote_asset_volume", "number_of_trades",
            "taker_buy_base_asset_volume", "taker_buy_quote_asset_volume",
            "ignore_col"
        )

        print(f"Sauvegarde des données Parquet dans {output_path}...")
        # Spark écrit un répertoire, pas un fichier unique par défaut
        # pour Parquet
        final_df.write.mode("overwrite").parquet(output_path)
        print(f"Données sauvegardées dans {output_path}")
        return output_path  # Retourne le chemin du répertoire Parquet

    def fill_table_from_spark_parquet(parquet_dir_path):
        print(f"Lecture des données Parquet de {parquet_dir_path} "
              "avec Spark...")
        loaded_df = spark.read.parquet(parquet_dir_path)

        print("Insertion des données de Parquet vers TimescaleDB "
              "avec Spark JDBC...")

        # Mode d'écriture: append. La gestion des conflits est faite
        # avec `ON CONFLICT DO NOTHING` dans la DB.
        # Il faut s'assurer que la table 'btcusdt' existe
        # avec la clé primaire sur 'open_time'.
        print("Lecture des clés existantes depuis TimescaleDB "
              "pour éviter les doublons...")
        existing_keys_df = spark.read.jdbc(
            url=db_url,
            # Subquery pour lire seulement la clé
            table="(SELECT open_time FROM btcusdt) as existing_keys",
            properties=db_properties
        )

        new_data_df = loaded_df.join(
            existing_keys_df,
            loaded_df.open_time == existing_keys_df.open_time,
            # Garde seulement les lignes de loaded_df
            # qui n'ont pas de correspondance
            "left_anti"
        )

        print(f"Nombre de nouvelles lignes à insérer: {new_data_df.count()}")
        
        if new_data_df.count() > 0:
            new_data_df.write.jdbc(
                url=db_url,
                table="btcusdt",
                mode="append",
                properties=db_properties
            )
            print("Nouvelles données insérées dans TimescaleDB.")
        else:
            print("Aucune nouvelle donnée à insérer.")

    # --- Exécution du script ---
    print("Récupération du dernier open_time depuis la base de données...")
    last_open_time_ms = get_last_open_time_from_db(
        spark, db_url, db_properties
    )

    print("Collecte des données depuis Binance...")
    # Utiliser la fonction get_historical_data globale
    # et passer last_open_time_ms
    klines = get_historical_data(
        start_after_timestamp_ms=last_open_time_ms
    )

    if klines:
        print(f"{len(klines)} klines collectées.")

        # Le nom du répertoire Parquet sera unique pour éviter les conflits
        # si on ne nettoie pas
        # timestamp_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        # spark_parquet_output_path = os.path.join(
        #     spark_output_parquet_dir,
        #     f"btcusdt_klines_spark_{timestamp_str}"
        # )
        # Pour simplifier, utilisons un nom de répertoire fixe pour
        # l'instant, car on utilise overwrite.
        # Ce chemin est relatif à ce que Spark voit,
        # donc SPARK_DATA_PATH/...
        spark_parquet_output_path = spark_output_parquet_dir

        print("Conversion DF Spark et sauvegarde en Parquet...")
        klines_to_spark_df_and_save_parquet(klines, spark_parquet_output_path)

        print("Vérification/Création table historique TimescaleDB...")
        # S'assure que la table et l'hypertable existent
        create_historic_table_if_not_exists()

        print("Insertion données Parquet vers TimescaleDB via Spark...")
        fill_table_from_spark_parquet(spark_parquet_output_path)

        print("Processus de données terminé.")
    else:
        print("Aucune kline n'a été collectée.")


if __name__ == "__main__":
    spark_session = None  # Initialiser pour le bloc finally
    try:
        spark_session = get_spark_session()
        run(spark_session)
    finally:
        if spark_session:
            spark_session.stop()
            print("Spark session stopped.")
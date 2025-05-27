import os
from datetime import datetime, timedelta

from airflow import DAG
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator

# Clés API (non utilisées par le script de streaming, mais passées par cohérence)
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY", "YOUR_SPARK_JOB_API_KEY")
BINANCE_API_SECRET = os.getenv("BINANCE_API_SECRET", "YOUR_SPARK_JOB_API_SECRET")
# JAVA_HOME: Ajustez si celui dans l'image Airflow est différent
JAVA_HOME = os.getenv("JAVA_HOME", "/usr/lib/jvm/java-17-openjdk-arm64") 
# Pour amd64: /usr/lib/jvm/java-17-openjdk-amd64

# Le master Spark et le deployMode devraient être définis par la connexion 'spark_default' dans l'UI Airflow
SPARK_APPLICATION_PATH = "/opt/bitnami/spark/data/kafka_to_timescale_streaming.py"
SPARK_PACKAGES = "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0"

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2023, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    dag_id='process_binance_streaming_data_spark',
    default_args=default_args,
    schedule_interval=None,
    catchup=False,
    tags=['spark', 'streaming', 'kafka', 'timescale'],
    doc_md="""
    ### DAG de traitement des données de streaming Binance avec Spark
    Ce DAG lance un job Spark Streaming qui :
    1. Lit les données de klines Binance depuis un topic Kafka.
    2. Transforme les données.
    3. Écrit les données transformées dans TimescaleDB.
    Le job Spark est conçu pour tourner en continu.
    """
) as dag:

    submit_spark_streaming_job = SparkSubmitOperator(
        task_id='submit_kafka_to_timescaledb_job',
        application=SPARK_APPLICATION_PATH,
        conn_id='spark_default',  # Utilisation de la connexion par défaut
        application_args=[],
        packages=SPARK_PACKAGES,
        conf={ 
            # Le master et le deploy-mode sont gérés par la connexion 'spark_default'
            # définie via AIRFLOW_CONN_SPARK_DEFAULT dans docker-compose.yml
        },
        env_vars={
            "BINANCE_API_KEY": BINANCE_API_KEY,
            "BINANCE_API_SECRET": BINANCE_API_SECRET,
            "JAVA_HOME": JAVA_HOME
        },
        verbose=True,
    ) 
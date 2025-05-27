from __future__ import annotations

import pendulum
import os
from datetime import timedelta

from airflow.models.dag import DAG
from airflow.providers.apache.spark.operators.spark_submit import (
    SparkSubmitOperator
)
# from airflow.utils.dates import days_ago # Import non utilisé

# Récupérer les clés API depuis les variables d'environnement
# configurées pour Airflow. Ces variables doivent être définies
# dans docker-compose.yml pour les services Airflow.
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY", "YOUR_DEFAULT_KEY")
BINANCE_API_SECRET = os.getenv("BINANCE_API_SECRET", "YOUR_DEFAULT_SECRET")

# JAVA_HOME pour l'environnement Spark, devrait correspondre à celui de l'image Airflow (Java 17)
JAVA_HOME_SPARK = os.getenv("JAVA_HOME", "/usr/lib/jvm/java-17-openjdk-arm64") 
# Ajustez si le JAVA_HOME dans votre image Airflow est différent pour Java 17 (ex: amd64)

with DAG(
    dag_id="process_historical_data_spark",
    schedule=timedelta(minutes=15),
    start_date=pendulum.datetime(2023, 10, 26, tz="UTC"),  # Date de début
    catchup=False,
    tags=["data_processing", "spark"],
) as dag:
    submit_spark_job = SparkSubmitOperator(
        task_id="submit_binance_data_processing_job",
        # Chemin vers script PySpark dans les conteneurs Spark
        application="/opt/bitnami/spark/data/binance_to_db.py",
        # Connexion Spark définie dans l'UI Airflow (Admin -> Connections)
        conn_id="spark_default",  # Utilisation de la connexion par défaut
        application_args=[],  # Arguments pour le script Spark si besoin
        conf={ 
            # Le master et le deploy-mode sont gérés par la connexion 'spark_default'
            # définie via AIRFLOW_CONN_SPARK_DEFAULT dans docker-compose.yml
        },
        # S'assure que le driver JDBC est sur tous les classpaths Spark
        jars="/opt/bitnami/spark/jars/postgresql-42.7.3.jar",
        # Passer les variables d'environnement au job Spark.
        # Le script python accède à ces variables via os.getenv()
        env_vars={
            "BINANCE_API_KEY": BINANCE_API_KEY,
            "BINANCE_API_SECRET": BINANCE_API_SECRET,
            "JAVA_HOME": JAVA_HOME_SPARK # Utiliser le JAVA_HOME de l'environnement Airflow (Java 17)
        },
        verbose=True,  # Logs détaillés du SparkSubmitOperator
    ) 
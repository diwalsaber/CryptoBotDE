from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.utils.dates import days_ago
from datetime import datetime, timedelta
from binance.client import Client
import psycopg2

# Initialise le client Binance
client = Client(api_key='your_api_key', api_secret='your_api_secret')

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': days_ago(1), # datetime(2021, 8, 6),
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'update_btcusdt', default_args=default_args, schedule_interval=timedelta(minutes=15))

def update_btcusdt(ds, **kwargs):
    # Get the latest klines
    klines = client.get_klines(symbol="BTCUSDT", interval=Client.KLINE_INTERVAL_15MINUTE, limit=1)

    # Initialise the database connection
    conn = psycopg2.connect(
        host='timescaledb',
        port=5432,
        dbname='postgres',
        user='postgres',
        password='postgres'
    )
    cur = conn.cursor()

    # Insert the data into the database
    # Insert the data into the database
    for kline in klines:
        try:
            cur.execute("""
                INSERT INTO btcusdt VALUES (
                    to_timestamp(%s / 1000), %s, %s, %s, %s, %s, to_timestamp(%s / 1000), %s, %s, %s, %s, %s
                )
            """, kline)
        except psycopg2.errors.UniqueViolation:
            print(f"Data for {kline[0]} already exists in the table. Skipped insertion.")
            conn.rollback()
            continue

    # Commit the changes and close the connection
    conn.commit()
    cur.close()
    conn.close()

    print(f"Data updated for date {ds}")

update_btcusdt_task = PythonOperator(
    task_id='update_btcusdt_task',
    provide_context=True,
    python_callable=update_btcusdt,
    dag=dag)

update_btcusdt_task

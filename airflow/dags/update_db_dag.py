import os
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.utils.dates import days_ago
from datetime import datetime, timedelta
from binance.client import Client
import psycopg2

# Récupérer les clés API depuis les variables d'environnement
# Fallback au cas où non défini
API_KEY = os.getenv('BINANCE_API_KEY', 'your_api_key')
API_SECRET = os.getenv('BINANCE_API_SECRET', 'your_api_secret')

# Initialise le client Binance
client = Client(api_key=API_KEY, api_secret=API_SECRET)

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': days_ago(1),
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'update_btcusdt',
    default_args=default_args,
    schedule_interval=timedelta(minutes=15),
    catchup=False  # Évite les exécutions passées au redémarrage
)

dag.doc_md = """
### DAG de Mise à Jour des Données BTC/USDT

Ce DAG est responsable de la mise à jour incrémentale des données de marché pour la paire BTC/USDT.

Il s'exécute toutes les 15 minutes pour récupérer les dernières bougies depuis l'API Binance
et les insérer dans la base de données TimescaleDB.

**Variables d'environnement requises pour le client Binance :**
- `BINANCE_API_KEY`
- `BINANCE_API_SECRET`
"""

def update_btcusdt(ds, **kwargs):
    """
    Tâche Python exécutée par Airflow pour récupérer et stocker les dernières données klines.

    Se connecte à l'API Binance, récupère les 2 dernières bougies de 15 minutes
    pour BTC/USDT, et les insère dans la table `btcusdt` de la base TimescaleDB.
    Gère les conflits pour éviter les insertions dupliquées.
    Des logs détaillés sont émis pour suivre le processus.
    """
    print(f"Tentative de mise à jour pour BTCUSDT à {datetime.now()}")
    # Afficher une partie de la clé pour vérification (NE PAS LOGUER EN PRODUCTION)
    api_key_start = API_KEY[:5]
    print(f"Clé API (début): {api_key_start}...")

    try:
        # Récupérer les 2 dernières bougies pour référence
        klines = client.get_klines(
            symbol="BTCUSDT",
            interval=Client.KLINE_INTERVAL_15MINUTE,
            limit=2
        )
        print("Klines reçues de Binance:")
        print(klines)

        if not klines:
            print("Aucune kline reçue de Binance.")
            return

        conn = psycopg2.connect(
            host='timescaledb', port=5432, dbname='postgres',
            user='postgres', password='postgres'
        )
        cur = conn.cursor()
        print("Connexion à la base de données TimescaleDB réussie.")

        insert_count = 0
        for kline in klines:
            try:
                # ON CONFLICT gère les doublons
                cur.execute("""
                    INSERT INTO btcusdt VALUES (
                        to_timestamp(%s / 1000), %s, %s, %s, %s, %s,
                        to_timestamp(%s / 1000), %s, %s, %s, %s, %s
                    ) ON CONFLICT (open_time) DO NOTHING;
                """, kline)
                if cur.rowcount > 0:
                    insert_count += 1
            except psycopg2.Error as e:
                print(f"Erreur BDD pour kline {kline[0]}: {e}")
                conn.rollback()  # Rollback la transaction partielle
                # Si une insertion échoue, les autres peuvent continuer
                # ou vous pourriez décider de stopper tout le lot.
                continue
        
        conn.commit()  # Commit toutes les insertions valides
        print(f"{insert_count} nouvelle(s) kline(s) insérée(s).")

        cur.close()
        conn.close()
        print("Connexion à la base de données fermée.")

    except Exception as e:
        print(f"Erreur générale dans update_btcusdt: {e}")
        raise  # Permet à Airflow de marquer la tâche comme échouée

    print(f"Mise à jour des données terminée pour {ds} ({datetime.now()})")

update_btcusdt_task = PythonOperator(
    task_id='update_btcusdt_task',
    provide_context=True,
    python_callable=update_btcusdt,
    dag=dag
)

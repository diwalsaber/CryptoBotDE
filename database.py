import pandas as pd
import psycopg2



# Lire le fichier CSV
csv_file = 'candles.csv'
df = pd.read_csv(csv_file)

# Créer une connexion à la base de données PostgreSQL
conn = psycopg2.connect(host="localhost", dbname="postgres")

cur = conn.cursor()

table = 'ma_table'

# Construire la requête de création de la table avec les noms de colonnes et types de données
create_table_query = f"CREATE TABLE IF NOT EXISTS {'ma_table'} ("
for col in df.columns:
    create_table_query += f"{col} DOUBLE PRECISION,"
create_table_query = create_table_query.rstrip(',') + ");"

# Créer la table dans la base de données
cur.execute(create_table_query)

# Insérer les données du fichier CSV dans la table
for index, row in df.iterrows():
    insert_query = f"INSERT INTO {table} ({', '.join(df.columns)}) VALUES ({', '.join(['%s' for _ in row])})"
    cur.execute(insert_query, tuple(row))

# Construire et exécuter la requête SQL
query = f"SELECT * FROM {table} WHERE close > 1000;"
cur.execute(query)

# Récupérer et afficher les résultats
results = cur.fetchall()
for row in results:
    print(row)

# Valider les modifications et fermer la connexion
conn.commit()
cur.close()
conn.close()
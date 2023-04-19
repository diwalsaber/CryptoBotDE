import psycopg2

conn = psycopg2.connect(
    host="localhost",
    port="5432",
    database="postgres",
    user="postgres",
    password="postgres"
)

cur = conn.cursor()
cur.execute("SELECT * FROM CandlestickHistorical LIMIT 0")

# Récupération des noms de colonnes
colnames = [desc[0] for desc in cur.description]
print(colnames)

cur.close()
conn.close()
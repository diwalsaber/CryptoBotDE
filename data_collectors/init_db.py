from data_collectors.cryptoutils import DBTools, Configuration


def init_symbols():
    try:
        conf = Configuration.get_instance()
        connection = DBTools.get_connection()
        cursor = connection.cursor()
        for pair_conf in conf.pairs_conf:
            if exists(cursor, pair_conf.symbol):
                # Update existing
                cursor.execute("UPDATE Symbol set Description = '{}' where Name = '{}'"
                        .format(pair_conf.description, pair_conf.symbol))
            else:
                # Create new
                cursor.execute("INSERT INTO Symbol (SymbolId, Name, Description) VALUES (nextval('seq_symbol'), '{}', '{}')".format(pair_conf.symbol, pair_conf.description))
        connection.commit()
    finally:
        cursor.close()
        DBTools.return_connection(connection)
def exists(cur, symbol):
    query = "select * from Symbol where name ='{}'".format(symbol)
    cur.execute(query)
    mobile_records = cur.fetchall()
    return len(mobile_records)  > 0

init_symbols()



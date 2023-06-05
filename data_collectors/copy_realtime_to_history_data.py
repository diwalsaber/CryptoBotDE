import psycopg2

from cryptobot.common.cryptoutils import DBConnector


def copy_to_history():
    try:
        connection = DBConnector.get_data_db_connection()
        cursor = connection.cursor()
        #copy real time data into history table
        cursor.execute("""INSERT INTO CandleStickHistorical SELECT * from CandlestickRealTime 
                       WHERE OPENTIME NOT IN (SELECT OPENTIME FROM CandleStickHistorical WHERE OPENTIME >= CURRENT_TIMESTAMP - INTERVAL '5 days')""")
        # delete copied data from real time table avoiding newly inserted data
        cursor.execute("""DELETE FROM CandlestickRealTime WHERE OPENTIME IN 
                       (SELECT OPENTIME from CandleStickHistorical WHERE OPENTIME >= (SELECT MIN(OPENTIME) FROM CandlestickRealTime))""")
        connection.commit()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        DBConnector.return_data_db_connection(connection)

copy_to_history()

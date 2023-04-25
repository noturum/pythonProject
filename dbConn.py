import sqlite3
from sqlite3 import Error, OperationalError
import redis


#redis_url = 'redis://127.0.0.1:6379/'

#redis_client = redis.from_url(redis_url,db=0, decode_responses=True)


def connDB():
    try:
        conn = sqlite3.connect('keys.db', isolation_level=None)
        cursor = conn.cursor()

        return conn, cursor
    except Error as e:
        print('Error db')
        
def executeSql(sql,commit:bool=False):
    #try:
    conn, cursor = connDB()
    cursor.execute(sql)
    if commit == True:
        conn.commit()
    # conn.close()

    return cursor.fetchall()
    #except OperationalError as s:
        #print('operation error')
        #print(s)
        #return 'error'

import sqlite3
from sqlite3 import Error, OperationalError
from settings import bot
import keyboards
from datetime import datetime, timedelta
from random import randint

def connDB():
    try:
        conn = sqlite3.connect('db_call.db', isolation_level=None)
        cursor = conn.cursor()

        return conn, cursor
    except Error as e:
        print('Error db')
def executeSql(sql,commit:bool=False):
    try:
        conn, cursor = connDB()
        cursor.execute(sql)
        if commit == True:
            conn.commit()
        # conn.close()

        return cursor.fetchall()
    except OperationalError as s:
        print('operation error')
        return 'error'
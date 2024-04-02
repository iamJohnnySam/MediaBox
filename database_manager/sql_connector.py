import threading
from functools import cache

import mysql.connector

from passwords import database_user, database_password
from tools.logger import log

lock = threading.Lock()


# http://192.168.1.32/phpmyadmin

class SQLConnector:

    def __init__(self, user, password, db=None, host="localhost"):
        self.user = user
        self.password = password
        self.database = db
        self.host = host

        if db is None:
            self.my_db = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                buffered=True
            )
        else:
            self.my_db = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database
            )
        self.cursor = self.my_db.cursor()

    def reconnect(self):
        del self.my_db
        self.my_db = mysql.connector.connect(
            host=self.host,
            user=self.user,
            password=self.password,
            database=self.database
        )
        self.cursor = self.my_db.cursor()

    @cache
    def get_databases(self):
        if self.database is None:
            self.cursor.execute("SHOW DATABASES")
            result = self.cursor.fetchall()
            return [row[0] for row in result]

    @cache
    def check_table_exists(self, table, job_id=0):
        lock.acquire()

        try:
            self.cursor.execute("SHOW TABLES")
        except mysql.connector.Error as err:
            log(job_id=job_id, msg=f'SQL Error: {str(err)}')
            self.reconnect()
            self.cursor.execute("SHOW TABLES")

        lock.release()

        if table not in self.cursor:
            return False
        else:
            return True

    def get_last_id(self, table, id_column, job_id=0):
        lock.acquire()
        query = f'SELECT {id_column} FROM {table} ORDER BY {id_column} DESC LIMIT 1;'

        try:
            self.cursor.execute(query)
        except mysql.connector.Error as err:
            log(job_id=job_id, msg=f'SQL Error: {str(err)}', error_code=10002)
            self.reconnect()
            try:
                self.cursor.execute(query)
            except mysql.connector.Error as err:
                log(job_id=job_id, msg=f'SQL Error: {str(err)}', error_code=10003)

        result = self.cursor.fetchone()
        lock.release()

        if result is None:
            return 0
        else:
            return result[0]

    def exists(self, table, where, job_id=0):
        lock.acquire()
        query = f"SELECT COUNT(1) FROM {table} WHERE {where};"

        try:
            self.cursor.execute(query)
        except mysql.connector.Error as err:
            log(job_id=job_id, msg=f'SQL Error: {str(err)}')
            self.reconnect()
            self.cursor.execute(query)

        result = self.cursor.fetchone()
        lock.release()

        log(job_id=job_id, msg=f'SQL > {query} | Result > {result}')
        return result[0]

    def run_sql(self, query, fetch_all=False, job_id=0):
        log(job_id=job_id, msg=query)
        lock.acquire()
        try:
            self.cursor.execute(query)
        except mysql.connector.Error as err:
            log(job_id=job_id, msg=f'SQL Error: {str(err)}')
            lock.release()
            self.reconnect()
            lock.acquire()
            self.cursor.execute(query)

        if query.startswith("DELETE") or query.startswith("UPDATE"):
            self.my_db.commit()
            if self.cursor.rowcount == 0:
                log(job_id=job_id, error_code=50003)
            result = "DONE"
            log(job_id=job_id, msg=str(self.cursor.rowcount) + " record(s) affected")

        elif query.startswith("SELECT"):
            if fetch_all:
                result = self.cursor.fetchall()
                log(job_id=job_id, msg=str(len(result)) + " record(s) retrieved")
            else:
                result = self.cursor.fetchone()
                log(job_id=job_id, msg=str(result))

        else:
            result = "error"

        lock.release()
        return result

    def insert(self, table, columns, val, get_id=False, id_column=None, job_id=0):
        lock.acquire()
        placeholder = "%s"
        for i in range(columns.count(",")):
            placeholder = placeholder + ", %s"

        sql = "INSERT INTO " + table + " (" + columns + ") VALUES (" + placeholder + ")"

        try:
            self.cursor.execute(sql, val)
        except mysql.connector.Error as err:
            log(job_id=job_id, msg=f'SQL Error: {str(err)}')
            self.reconnect()
            self.cursor.execute(sql, val)

        log(job_id=job_id, msg=f'SQL > {sql} \tID > {self.cursor.lastrowid}')
        self.my_db.commit()

        if get_id:
            self.cursor.execute(f'SELECT {id_column} FROM {table} ORDER BY {id_column} DESC LIMIT 1')
            result = self.cursor.fetchone()
            last_id = result[0]
            lock.release()
            return True, last_id

        lock.release()
        return True, self.cursor.lastrowid


db_all = SQLConnector(database_user, database_password)
database_list = db_all.get_databases()

sql_databases = {}
for database in database_list:
    if database == 'information_schema':
        continue
    sql_databases[database] = SQLConnector(database_user, database_password, database)

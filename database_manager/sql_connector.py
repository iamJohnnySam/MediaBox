import threading

import mysql.connector

import logger
import settings
from maintenance.backup import backup


# http://192.168.1.32/phpmyadmin

class SQLConnector:

    def __init__(self, user, password, database=None, host="localhost"):
        self.user = user
        self.password = password
        self.database = database
        self.host = host

        if database is None:
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

        self.lock = threading.Lock()

    def reconnect(self):
        del self.my_db
        self.my_db = mysql.connector.connect(
            host=self.host,
            user=self.user,
            password=self.password,
            database=self.database
        )
        self.cursor = self.my_db.cursor()

    def get_databases(self):
        if self.database is None:
            self.cursor.execute("SHOW DATABASES")
            result = self.cursor.fetchall()
            return [row[0] for row in result]

    def check_table_exists(self, table):
        self.lock.acquire()

        try:
            self.cursor.execute("SHOW TABLES")
        except mysql.connector.Error as err:
            logger.log(f'SQL Error: {str(err)}')
            self.reconnect()
            self.cursor.execute("SHOW TABLES")

        self.lock.release()

        if table not in self.cursor:
            return False
        else:
            return True

    def get_last_id(self, table, id_column):
        self.lock.acquire()
        query = f'SELECT {id_column} FROM {table} ORDER BY {id_column} DESC LIMIT 1;'

        try:
            self.cursor.execute(query)
        except mysql.connector.Error as err:
            logger.log(f'SQL Error: {str(err)}')
            self.reconnect()
            self.cursor.execute(query)

        result = self.cursor.fetchone()
        self.lock.release()

        if result is None:
            return 0
        else:
            return result[0]

    def exists(self, table, where):
        self.lock.acquire()
        query = f"SELECT COUNT(1) FROM {table} WHERE {where};"

        try:
            self.cursor.execute(query)
        except mysql.connector.Error as err:
            logger.log(f'SQL Error: {str(err)}')
            self.reconnect()
            self.cursor.execute(query)

        result = self.cursor.fetchone()
        self.lock.release()

        logger.log(f'SQL > {query} | Result > {result}')
        return result[0]

    def run_sql(self, query, fetch_all=False):
        self.lock.acquire()
        try:
            self.cursor.execute(query)
        except mysql.connector.Error as err:
            logger.log(f'SQL Error: {str(err)}')
            self.reconnect()
            self.cursor.execute(query)

        logger.log(query)

        if query.startswith("DELETE") or query.startswith("UPDATE"):
            self.my_db.commit()
            result = "DONE"
            logger.log(str(self.cursor.rowcount) + " record(s) affected")

        elif query.startswith("SELECT"):
            if fetch_all:
                result = self.cursor.fetchall()
                logger.log(str(len(result)) + " record(s) retrieved")
            else:
                result = self.cursor.fetchone()
                logger.log(str(result))

        else:
            result = "error"

        self.lock.release()
        return result

    def insert(self, table, columns, val, get_id=False, id_column=None):
        self.lock.acquire()
        placeholder = "%s"
        for i in range(columns.count(",")):
            placeholder = placeholder + ", %s"

        sql = "INSERT INTO " + table + " (" + columns + ") VALUES (" + placeholder + ")"

        try:
            self.cursor.execute(sql, val)
        except mysql.connector.Error as err:
            logger.log(f'SQL Error: {str(err)}')
            self.reconnect()
            self.cursor.execute(sql, val)

        logger.log(f'SQL > {sql} \tID > {self.cursor.lastrowid}')
        self.my_db.commit()

        if get_id:
            self.cursor.execute(f'SELECT {id_column} FROM {table} ORDER BY {id_column} DESC LIMIT 1')
            result = self.cursor.fetchone()
            last_id = result[0]
            self.lock.release()
            return True, last_id

        self.lock.release()
        return True, self.cursor.lastrowid


db_all = SQLConnector(settings.database_user, settings.database_password)
database_list = db_all.get_databases()

sql_databases = {}
for database in database_list:
    if database == 'information_schema':
        continue
    sql_databases[database] = SQLConnector(settings.database_user, settings.database_password, database)
    backup.databases.append(database)

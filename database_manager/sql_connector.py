import mysql.connector

import logger


# http://192.168.1.32/phpmyadmin

class SQLConnector:

    def __init__(self, user, password, database, host="localhost"):
        self.my_db = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=database
        )
        self.database = database
        self.cursor = self.my_db.cursor()

    def check_table_exists(self, table):
        self.cursor.execute("SHOW TABLES")
        if table not in self.cursor:
            return False
        else:
            return True

    def get_last_id(self, table, id_column):
        query = f'SELECT {id_column} FROM {table} ORDER BY {id_column} DESC LIMIT 1;'
        self.cursor.execute(query)
        result = self.cursor.fetchone()
        if result is None:
            return 0
        else:
            return result[0]

    def check_exists(self, table, where):
        query = f"SELECT COUNT(1) FROM {table} WHERE {where};"
        self.cursor.execute(query)
        result = self.cursor.fetchone()
        logger.log(f'SQL > {query} | Result > {result}')
        return result[0]

    def run_sql(self, query, fetch_all=False):
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

        return result

    def insert(self, table, columns, val, get_id=False, id_column=None):
        placeholder = "%s"
        for i in range(columns.count(",")):
            placeholder = placeholder + ", %s"

        sql = "INSERT INTO " + table + " (" + columns + ") VALUES (" + placeholder + ")"
        self.cursor.execute(sql, val)
        logger.log(f'SQL > {sql} \tID > {self.cursor.lastrowid}')
        self.my_db.commit()

        if get_id:
            self.cursor.execute(f'SELECT {id_column} FROM {table} ORDER BY {id_column} DESC LIMIT 1')
            result = self.cursor.fetchone()
            last_id = result[0]
            return True, last_id

        return True, self.cursor.lastrowid

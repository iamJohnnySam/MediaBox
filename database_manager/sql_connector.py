import mysql.connector

import logger
import settings


# http://192.168.1.32/phpmyadmin

class SQLConnector:
    source = "SQL"

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

    def run_sql(self, query):
        self.cursor.execute(query)
        result = self.cursor.fetchone()
        logger.log(query, source=self.source)
        return result

    def insert(self, table, columns, val, get_id=False, id_column=None):
        placeholder = "%s"
        for i in range(columns.count(",")):
            placeholder = placeholder + ", %s"

        sql = "INSERT INTO " + table + " (" + columns + ") VALUES (" + placeholder + ")"
        self.cursor.execute(sql, val)
        logger.log(f'SQL > {sql} Inserted at {self.cursor.lastrowid}', source=self.source)
        self.my_db.commit()

        if get_id:
            self.cursor.execute(f'SELECT {id_column} FROM {self.database} ORDER BY ID DESC LIMIT 1')
            result = self.cursor.fetchone()
            last_id = result[0]
            return True, last_id

        return True, self.cursor.lastrowid




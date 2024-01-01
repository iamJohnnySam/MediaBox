import mysql.connector

import settings


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
        self.my_cursor = self.my_db.cursor()

    def check_table_exists(self, table):
        self.my_cursor.execute("SHOW TABLES")
        if table not in self.my_cursor:
            return False
        else:
            return True

    def insert(self, table, columns, val):
        placeholder = "%s"
        for i in range(columns.count(",")):
            placeholder = placeholder + ", %s"

        sql = "INSERT INTO " + table + " (" + columns + ") VALUES (" + placeholder + ")"
        self.my_cursor.execute(sql, val)
        self.my_db.commit()
        return True, self.my_cursor.lastrowid



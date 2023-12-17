import mysql.connector

import settings


class SQLConnector:
    def __init__(self, user, password, database):
        self.my_db = mysql.connector.connect(
            host="localhost",
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
        for i in columns.count(","):
            placeholder = placeholder + ", %s"

        sql = "INSERT INTO " + table + " (" + columns + ") VALUES (" + placeholder + ")"
        try:
            self.my_cursor.execute(sql, val)
            self.my_db.commit()
            return True, self.my_cursor.lastrowid

        except:
            return False, 0


finance_db = SQLConnector(settings.database_user, settings.database_password, 'transactions')


def insert(table, columns, values, model="finance"):
    if model == "finance":
        pass
    pass

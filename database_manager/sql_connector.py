import mysql.connector


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

    def insert(self, table, columns, val):
        placeholder = "%s"
        for i in columns.count(","):
            placeholder = placeholder + ", %s"

        sql = "INSERT INTO " + table + " (" + columns + ") VALUES (" + placeholder + ")"
        try:
            self.my_cursor.execute(sql, val)
            self.my_db.commit()
            return True
        except:
            return False

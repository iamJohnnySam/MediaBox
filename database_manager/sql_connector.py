import threading

import mysql.connector

import passwords
from tools.custom_exceptions import InvalidParameterException
from shared_tools.logger import log


# http://192.168.1.32/phpmyadmin

def replace_with_placeholder(columns, placeholder: str = '%s') -> str:
    string = placeholder
    for i in range(columns.count(",")):
        string = f"{string}, {placeholder}"
    return string


def generate_placeholder(fields: str | dict, concatenate=" AND "):
    string = ""
    val = ()

    if type(fields) == str:
        return fields, ()

    elif type(fields) == dict:
        for field in fields.keys():
            if string != "":
                string = f"{string}{concatenate}"
            string = f"{string}{field} = %s"
            value = fields[field]
            f_val = value if type(value) is str else str(value)
            val = val + (f_val,)
        return string, val
    else:
        raise InvalidParameterException("Invalid SQL Delete Command")


class SQLConnector:

    def __init__(self, job_id: int, user: str = None, password: str = None, database=None, host: str = "localhost"):
        self._job_id: int = job_id
        self.user = user if user is not None else passwords.database_user
        self.password = password if password is not None else passwords.database_password
        self.database = database
        self.host = host
        self.lock = threading.Lock()

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

    @property
    def job_id(self):
        return self._job_id

    @job_id.setter
    def job_id(self, a: int):
        self._job_id = a

    def check_connection(self):
        if not self.my_db.is_connected():
            self._reconnect()

    def _reconnect(self):
        self.lock.release()
        del self.my_db
        self.my_db = mysql.connector.connect(
            host=self.host,
            user=self.user,
            password=self.password,
            database=self.database
        )
        self.cursor = self.my_db.cursor()
        self.lock.acquire()

    def get_databases(self):
        if self.database is None:
            self.cursor.execute("SHOW DATABASES")
            result = self.cursor.fetchall()
            return [row[0] for row in result]

    def check_table_exists(self, table: str) -> bool:
        self.lock.acquire()
        try:
            self.cursor.execute("SHOW TABLES")
        except mysql.connector.Error as err:
            log(job_id=self._job_id, msg=f'SQL Error: {str(err)}', log_type="error")
            self._reconnect()
            self.cursor.execute("SHOW TABLES")
        self.lock.release()

        if table not in self.cursor:
            return False
        else:
            return True

    def get_last_id(self, table: str, id_column: str):
        self.lock.acquire()
        query = f"SELECT {id_column} FROM {table} ORDER BY {id_column} DESC LIMIT 1;"

        try:
            self.cursor.execute(query)
        except mysql.connector.Error as err:
            log(job_id=self._job_id, msg=f'SQL Error: {str(err)}', error_code=10002)
            self._reconnect()
            try:
                self.cursor.execute(query)
            except mysql.connector.Error as err:
                log(job_id=self._job_id, msg=f'SQL Error: {str(err)}', error_code=10003)

        result = self.cursor.fetchone()
        self.lock.release()

        if result is None:
            return 0
        else:
            return result[0]

    def insert(self, table: str, columns: str, val: tuple):
        sql = f"INSERT INTO {table} ({columns}) VALUES ({replace_with_placeholder(columns)})"
        self._run_sql_command(sql, val)
        return self.cursor.lastrowid

    def update(self, table: str, update: dict, where: str | dict):
        sql_update, val_update = generate_placeholder(update, ", ")
        val = val_update
        sql_where, val_where = generate_placeholder(where)
        val = val + val_where

        sql = f"UPDATE {table} SET {sql_update} WHERE {sql_where}"

        if val == ():
            self._run_sql_command(sql)
        else:
            self._run_sql_command(sql, val)

    def select(self, table: str, columns: str, where: str | dict = None,
               order: str = None, ascending: bool = True,
               limit: int = 0,
               fetch_all: bool = False):
        val = ()
        sql = f"SELECT {columns} FROM {table}"

        if where is not None:
            sql_where, val_where = generate_placeholder(where)
            val = val + val_where
            sql = f"{sql} WHERE {sql_where}"

        if order is not None:
            sql = f"{sql} ORDER BY {order}{'' if ascending else ' DESC'}"

        if limit != 0:
            sql = f"{sql} LIMIT {limit}"

        if val == ():
            self._run_sql_command(sql)
        else:
            self._run_sql_command(sql, val)

        if fetch_all:
            result = self.cursor.fetchall()
            log(job_id=self._job_id, msg=f'Result > {len(result)} record(s) retrieved.')
        else:
            result = self.cursor.fetchone()
            log(job_id=self._job_id, msg=f'Result > {result}.')
        return result

    def delete(self, table: str, where: str | dict) -> None:
        sql_where, val_where = generate_placeholder(where)
        sql = f"DELETE FROM {table} WHERE {sql_where}"
        if val_where == ():
            self._run_sql_command(sql)
        else:
            self._run_sql_command(sql, val_where)

    def check_exists(self, table: str, where: str | dict) -> int:
        sql_where, val_where = generate_placeholder(where)
        sql = f"SELECT COUNT(1) FROM {table} WHERE {sql_where}"
        if val_where == ():
            self._run_sql_command(sql)
        else:
            self._run_sql_command(sql, val_where)

        result = self.cursor.fetchone()
        log(job_id=self._job_id, msg=f'Result > {result[0]}.')
        return result[0]

    def create_table(self, tbl_name):
        log(job_id=self._job_id, msg=f'Creating table > {tbl_name}.')
        # todo
        # column_name_1 column_Data_type,
        # column_name_2 column_Data_type,
        # :
        # column_name_n column_Data_type

    def _run_sql_command(self, sql: str, val=None):
        self.check_connection()
        log(job_id=self._job_id, msg=f'SQL > {sql}')
        if val is not None:
            log(job_id=self._job_id, msg=f'SQL val > {val}')

        self.lock.acquire()

        try:
            if type(val) == tuple:
                self.cursor.execute(sql, val)
            else:
                self.cursor.execute(sql)
        except mysql.connector.Error as err:
            log(job_id=self._job_id, msg=f'SQL Error: {str(err)}', log_type="error")
            raise mysql.connector.Error

        if sql.startswith("DELETE") or sql.startswith("UPDATE") or sql.startswith("INSERT"):
            self.my_db.commit()
            if self.cursor.rowcount == 0:
                log(job_id=self._job_id, error_code=50003)

        self.lock.release()

        if self.cursor.rowcount != 0:
            log(job_id=self._job_id, msg=f'SQL > {self.cursor.rowcount} record(s) affected')
        if self.cursor.lastrowid != 0:
            log(job_id=self._job_id, msg=f'SQL ID > {self.cursor.lastrowid}')

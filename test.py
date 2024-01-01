import csv

import settings
from database_manager.sql_connector import SQLConnector


# python MediaBox/test/test.py

connector = SQLConnector(settings.database_user, settings.database_password, 'transactions')

with open('test/categories.csv', newline='') as csvfile:
    data = list(csv.reader(csvfile))

for row in data:
    val = (row[2], row[0], row[1])
    connector.insert(table='categories',
                     columns="`category`, `in_out`, `type`",
                     val=val)



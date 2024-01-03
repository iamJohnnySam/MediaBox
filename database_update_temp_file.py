import global_var
import settings
import csv
from database_manager.json_editor import JSONEditor
from database_manager.sql_connector import SQLConnector

sql = SQLConnector(settings.database_user, settings.database_password, 'transactions')

# data = JSONEditor(global_var.baby_feed_database).read()
# for key in data.keys():
#     columns = "date, time, amount, source"
#     val = (data[key]['date'], data[key]['time'], float(data[key]['ml']), data[key]['source'])
#     sql.insert('feed', columns, val)

# data = JSONEditor(global_var.baby_diaper_database).read()
# for key in data.keys():
#     columns = "date, time, what, count"
#     val = (data[key]['date'], data[key]['time'], data[key]['what'], 1)
#     sql.insert('diaper', columns, val)

# data = JSONEditor(global_var.baby_weight_database).read()
# for key in data.keys():
#     columns = "date, weight"
#     val = (key, float(data[key]))
#     sql.insert('weight', columns, val)

with open('temp/vendors.csv', newline='') as f:
    reader = csv.reader(f)
    data = list(reader)

for item in data:
    columns = "name"
    val = (item[0])
    sql.insert('vendors', columns, val)

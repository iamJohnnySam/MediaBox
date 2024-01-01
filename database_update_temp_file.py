import global_var
import settings
from database_manager.json_editor import JSONEditor
from database_manager.sql_connector import SQLConnector

sql = SQLConnector(settings.database_user, settings.database_password, 'baby')

data = JSONEditor(global_var.baby_feed_database).read()
for key in data.keys():
    columns = "date, time, amount, source"
    val = (data[key]['date'], data[key]['time'], float(data[key]['ml']), data[key]['source'])
    sql.insert('feed', columns, val)

data = JSONEditor(global_var.baby_diaper_database).read()
for key in data.keys():
    columns = "date, time, what, source"
    val = (data[key]['date'], data[key]['time'], data[key]['what'], 1)
    sql.insert('diaper', columns, val)

data = JSONEditor(global_var.baby_weight_database).read()
for key in data.keys():
    columns = "date, weight"
    val = (data[key]['date'], float(data[key]['weight']))
    sql.insert('weight', columns, val)

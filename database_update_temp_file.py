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

with open('temp/expenses.csv', newline='') as f:
    reader = csv.reader(f)
    data = list(reader)

# for item in data:
#     columns = "name"
#     val = (item[0], )
#     sql.insert('vendors', columns, val)

for item in data:
    query = f'SELECT category_id FROM categories WHERE category = "{data[2]}"'
    cat_id = list(sql.run_sql(query))[0]

    query = f'SELECT vendor_id FROM vendors WHERE name = "{data[4]}"'
    ven_id = list(sql.run_sql(query))[0]

    columns = "transaction_by, date, type, category_id, amount, vendor_id, foreign_amount, currency, " \
              "rate, comments"
    val = (str(settings.master),
           data[0],
           str(data[1]).lower,
           cat_id,
           data[3],
           ven_id,
           data[6],
           data[7],
           data[8],
           data[9])
    sql.insert('transactions_lkr', columns, val)

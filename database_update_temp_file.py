from datetime import datetime

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

with open('temp/expenses.csv', newline='', encoding='utf-8-sig') as f:
    reader = csv.reader(f)
    data = list(reader)

# for item in data:
#     columns = "name"
#     val = (item[0], )
#     sql.insert('vendors', columns, val)

for item in data:
    print(item)
    if item[2] == "":
        cat_id = None
    else:
        query = f'SELECT category_id FROM categories WHERE category = "{item[2]}"'
        cat_id = list(sql.run_sql(query))[0]

    if item[4] == "":
        ven_id = None
    else:
        query = f'SELECT vendor_id FROM vendors WHERE name = "{item[4]}"'
        ven_id = list(sql.run_sql(query))[0]

    tra = str(item[1]).lower()
    date = datetime.strptime(item[0], '%d/%m/%Y').strftime('%Y-%m-%d')

    if item[6] == "":
        fval = 0
    else:
        fval = float(item[6])

    if item[8] == "":
        rate = 0
    else:
        rate = item[8]

    print(cat_id, ven_id)

    columns = "transaction_by, date, type, category_id, amount, vendor_id, foreign_amount, currency, " \
              "rate, comments"
    val = (str(settings.master),
           date,
           tra,
           cat_id,
           float(item[3]),
           ven_id,
           fval,
           item[7],
           rate,
           item[9])
    print(val)
    sql.insert('transaction_lkr', columns, val)
    print()

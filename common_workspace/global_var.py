import multiprocessing

version = "3.0"

flag_stop: multiprocessing.Value = multiprocessing.Value('i', 0)
flag_restart: multiprocessing.Value = multiprocessing.Value('i', 0)
flag_reboot: multiprocessing.Value = multiprocessing.Value('i', 0)

default_port = 10000
socket_id = 0
main_telegram_channel = ""

date_formats = ["%Y-%m-%d", "%d-%m-%Y", "%Y-%b-%d", "%d-%b-%Y", "%m-%d-%y", "%b-%d-%y",
                "%Y/%m/%d", "%d/%m/%Y", "%Y/%b/%d", "%d/%b/%Y",
                "%m/%d", "%d/%m", "%b/%d", "%d/%b",
                "%m-%d", "%d-%m", "%b-%d", "%d-%b",
                "%Y,%m,%d", "%d,%m,%Y", "%Y,%b,%d", "%d,%b,%Y",
                "%m,%d", "%d,%m", "%b,%d", "%d,%b"]

time_formats = ["%H:%M:%S", "%H:%M",
                "%H-%M-%S", "%H-%M"]

currencies = ["LKR", "USD", "SGD", "EUR"]

credit_words = ["Credit", "inward slip transfer", "Int.Pd", "ISLI"]
debit_words = ["Debit", "trx", "transaction", "bill payment", "WTax.Pd"]

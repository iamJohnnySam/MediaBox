import platform

import refs
from tools.logger import log

operation_mode = True if platform.machine() == 'armv7l' else False
platform = platform.machine()

if not operation_mode:
    refs.main_channel = "test"
    log(msg="Main Channel switched")

ready_to_run = False
stop_all = False
restart = False
reboot_pi = False

date_formats = ["%Y-%m-%d", "%d-%m-%Y", "%Y-%b-%d", "%d-%b-%Y", "%m-%d-%y", "%b-%d-%y",
                "%Y/%m/%d", "%d/%m/%Y", "%Y/%b/%d", "%d/%b/%Y",
                "%m/%d", "%d/%m", "%b/%d", "%d/%b",
                "%m-%d", "%d-%m", "%b-%d", "%d-%b",
                "%Y,%m,%d", "%d,%m,%Y", "%Y,%b,%d", "%d,%b,%Y",
                "%m,%d", "%d,%m", "%b,%d", "%d,%b"]

time_formats = ["%H:%M:%S", "%H:%M",
                "%H-%M-%S", "%H-%M"]

credit_words = ["Credit", "inward slip transfer", "Int.Pd", "ISLI"]
debit_words = ["Debit", "trx", "transaction", "bill payment", "WTax.Pd"]

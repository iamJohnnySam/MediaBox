import threading

from common_workspace import queues, global_var
from shared_models import configuration
from shared_tools.logger import log
from web_handler.web import web_app


def main(message_q, job_q, packet_q, info_q, flag_stop, flag_restart, flag_reboot):
    queues.message_q = message_q
    queues.job_q = job_q
    queues.packet_q = packet_q
    queues.info_q = info_q
    global_var.flag_stop = flag_stop
    global_var.flag_restart = flag_restart
    global_var.flag_reboot = flag_reboot

    config = configuration.Configuration().web

    if config["enable"]:
        log(msg="Web Process is Starting...")

        t_webapp = threading.Thread(target=web_app.run_webapp, daemon=True)
        t_webapp.start()

        log(msg="Thread Started: Web app")

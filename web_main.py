from common_workspace import queues, global_var
from shared_models import configuration
from shared_tools.logger import log
from web_handler import web_app


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

        web_app.run_webapp()


if __name__ == '__main__':
    web_app.run_webapp()

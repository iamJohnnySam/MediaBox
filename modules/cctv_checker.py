import datetime
import time
import os

import global_variables
import passwords
import refs
from brains.job import Job
from communication.message import Message
from modules.base_module import Module
from tools.image_classifier import ImageClassifier
from communication.email_manager import EmailManager
from tools.logger import log


class CCTVChecker(Module):
    last_detect_A02 = None
    last_detect_A01 = None

    def __init__(self, job: Job):
        super().__init__(job)
        if not os.path.exists(refs.cctv_download):
            os.makedirs(refs.cctv_download)

        for f in os.listdir(refs.cctv_download):
            os.remove(os.path.join(refs.cctv_download, f))

        log(self._job.job_id, "Created Object")

    def download_cctv(self):
        log(self._job.job_id, "-------STARTED CCTV MAIN SCRIPT-------")

        cctv_classifier1 = ImageClassifier(self._job, refs.cctv_model1, "A01", 0.75)
        cctv_classifier2 = ImageClassifier(self._job, refs.cctv_model2, "A02", 0.75)

        client = EmailManager(self._job, passwords.gmail_em, passwords.gmail_pw, refs.cctv_mailbox)

        if client.connection_err > 0:
            del client
            log(self._job.job_id, "Deleted CCTV Object")
            time.sleep(10)
            client = EmailManager(self._job, passwords.outlook_em, passwords.outlook_pw, refs.cctv_mailbox)

        running = True
        sus_attachment_count: int = 0

        while running:
            running, attachment, date, file_n = client.get_next_attachment()

            if (not running) or global_variables.stop_all:
                break

            save_as = date + " " + file_n
            save_as = save_as.replace(",", "").replace(":", "-")
            att_path = os.path.join(refs.cctv_download, save_as)

            if not os.path.isfile(att_path):
                fp = open(att_path, 'wb')
                fp.write(attachment)
                fp.close()

            if "A01" in file_n:
                val, sus, location = cctv_classifier1.classify(att_path)
                if sus:
                    self.last_detect_A01 = datetime.datetime.now()
            elif "A02" in file_n:
                val, sus, location = cctv_classifier2.classify(att_path)
                if sus:
                    self.last_detect_A02 = datetime.datetime.now()
            else:
                val, sus, location = 0, 0, ""

            if sus:
                if sus_attachment_count == 0:
                    self.send_message(Message(date, job=self._job, group=refs.group_cctv))
                    sus_attachment_count = sus_attachment_count + 1
                self.send_message(Message(str(val), job=self._job,
                                          photo=att_path,
                                          group=refs.group_cctv))

            log(self._job.job_id, save_as + "\t SUS: " + str("%.2f" % val))
            try:
                os.remove(att_path)
            except PermissionError as e:
                if global_variables.operation_mode:
                    raise PermissionError
                else:
                    log(self._job.job_id, error_code=10001, error=str(e))
                    continue

        log(self._job.job_id, "-------ENDED CCTV MAIN SCRIPT-------")

    def get_last(self, amount: int):
        pass

    def clean_up(self, mailbox="Sent"):
        client = EmailManager(self._job, passwords.outlook_em, passwords.outlook_pw, mailbox)
        client.delete_all_emails(mailbox)

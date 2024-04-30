from datetime import datetime
import shutil
import os
from random import random

import global_variables
import passwords
from brains.job import Job
from communication.message import Message
from modules.base_module import Module
from tools import params
from tools.image_classifier import ImageClassifier
from communication.email_manager import EmailManager
from tools.logger import log


class CCTVChecker(Module):
    module = 'cctv'

    def __init__(self, job: Job):
        super().__init__(job)
        self.last_detect_A02 = None
        self.last_detect_A01 = None

        self.cctv_imap = params.get_param(self.module, 'imap')
        self.cctv_mailbox = params.get_param(self.module, 'mailbox')
        self.cctv_sent = params.get_param(self.module, 'sent')
        self.cctv_model1 = params.get_param(self.module, 'model1')
        self.cctv_model2 = params.get_param(self.module, 'model2')
        self.cctv_download = params.get_param(self.module, 'download_loc')
        self.cctv_save = params.get_param(self.module, 'save_loc')

        if not os.path.exists(self.cctv_download):
            os.makedirs(self.cctv_download)

        for f in os.listdir(self.cctv_download):
            os.remove(os.path.join(self.cctv_download, f))

        log(self._job.job_id, "Created Object")

    def download_cctv(self):
        log(self._job.job_id, "-------STARTED CCTV MAIN SCRIPT-------")

        cctv_classifier1 = ImageClassifier(self._job, self.cctv_model1, "A01")
        cctv_classifier2 = ImageClassifier(self._job, self.cctv_model2, "A02")

        client = EmailManager(self._job, passwords.gmail_em, self.cctv_imap, passwords.gmail_pw, self.cctv_mailbox)

        running = True

        while running:
            running, attachment, date, file_n = client.get_next_attachment()

            if (not running) or global_variables.stop_all:
                break

            save_as = date + " " + file_n
            save_as = save_as.replace(",", "").replace(":", "-")
            att_path = os.path.join(self.cctv_download, save_as)

            if not os.path.isfile(att_path):
                fp = open(att_path, 'wb')
                fp.write(attachment)
                fp.close()

            if "A01" in file_n:
                val, sus = cctv_classifier1.classify(att_path)
                if sus:
                    self.last_detect_A01 = datetime.now()
                    sav_cctv = os.path.join(self.cctv_save, "A01", "1")
                else:
                    sav_cctv = os.path.join(self.cctv_save, "A01", "0")
            elif "A02" in file_n:
                val, sus = cctv_classifier2.classify(att_path)
                if sus:
                    self.last_detect_A02 = datetime.now()
                    sav_cctv = os.path.join(self.cctv_save, "A02", "1")
                else:
                    sav_cctv = os.path.join(self.cctv_save, "A02", "0")
            else:
                continue

            if sus or (not sus and random() > 0.75):
                if not os.path.exists(sav_cctv):
                    os.makedirs(sav_cctv)

                file_name = f"{datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}-{date}-{val:.3f}.jpg"
                t = 1
                while os.path.isfile(os.path.join(sav_cctv, file_name)):
                    file_name = f"{datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}-{date}-{val:.3f}({t}).jpg"
                    t = t+1
                file_name = file_name.replace(":", "").replace(" ", "")
                move_destination = shutil.move(att_path, os.path.join(sav_cctv, file_name))
                log(self._job.job_id, f"Image Saved in {move_destination} with sus level at {val:.3f}")

        log(self._job.job_id, "-------ENDED CCTV MAIN SCRIPT-------")
        client.email_close()

    def get_last(self, amount: int = 10):
        a01_files = sorted(os.listdir(os.path.join(self.cctv_save, "A01", "1")))[-amount:]
        a02_files = sorted(os.listdir(os.path.join(self.cctv_save, "A02", "1")))[-amount:]

        self.send_message(Message(job=self._job, send_string=f"Last {amount} CCTV images for A01 channel."))
        for photo in a01_files:
            self.send_message(Message(job=self._job, send_string=photo,
                                      photo=os.path.join(self.cctv_save, "A01", "1", photo)))

        self.send_message(Message(job=self._job, send_string=f"Last {amount} CCTV images for A02 channel."))
        for photo in a02_files:
            self.send_message(Message(job=self._job, send_string=photo,
                                      photo=os.path.join(self.cctv_save, "A02", "1", photo)))

        else:
            log(self._job.job_id, f"Cannot get last {amount} CCTV images. Not in Operation Mode")

    def clean_up(self, mailbox=""):
        if mailbox == "":
            mailbox = self.cctv_sent
        client = EmailManager(self._job, passwords.gmail_em, self.cctv_imap, passwords.gmail_pw, mailbox)
        client.delete_all_emails(mailbox)
        client.email_close()
        self._job.complete()

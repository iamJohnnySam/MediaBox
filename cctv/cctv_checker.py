import datetime
import email
import imaplib
import os
import settings
import communicator
import logger
from cctv.image_classifier import ImageClassifier


class CCTVChecker:
    def __init__(self):
        self.last_detect_A02 = None
        self.last_detect_A01 = None
        self.connection_err = 0

        self.cctv_classifier1 = ImageClassifier(settings.cctv_model1, "A01", 0.75)
        self.cctv_classifier2 = ImageClassifier(settings.cctv_model2, "A02", 0.75)

        if not os.path.exists(settings.cctv_download):
            os.makedirs(settings.cctv_download)

        for f in os.listdir(settings.cctv_download):
            os.remove(os.path.join(settings.cctv_download, f))

        self.outlook = imaplib.IMAP4_SSL('outlook.office365.com', 993)
        self.log_in()

    def log_in(self):
        try:
            self.outlook.login(settings.em, settings.pw)
        except imaplib.IMAP4.error:
            print("Logged In")

    def get_attachment(self, msg, date):
        sus_attachment_count: int = 0
        for part in msg.walk():
            if part.get_content_maintype() == 'multipart':
                continue
            if part.get('Content-Disposition') is None:
                continue

            file_n = part.get_filename()
            save_as = date + " " + file_n
            save_as = save_as.replace(",", "").replace(":", "-")
            att_path = os.path.join(settings.cctv_download, save_as)

            if not os.path.isfile(att_path):
                fp = open(att_path, 'wb')
                fp.write(part.get_payload(decode=True))
                fp.close()

            if "A01" in file_n:
                val, sus, location = self.cctv_classifier1.classify(att_path)
                if sus:
                    self.last_detect_A01 = datetime.datetime.now()
            elif "A02" in file_n:
                val, sus, location = self.cctv_classifier2.classify(att_path)
                if sus:
                    self.last_detect_A02 = datetime.datetime.now()
            else:
                val, sus, location = 0, 0, ""

            if sus:
                if sus_attachment_count == 0:
                    communicator.send_now(date, "cctv", cctv=True)
                    sus_attachment_count = sus_attachment_count + 1
                communicator.send_now(att_path, "cctv", img=True, cctv=True)
                communicator.send_now(str(val), "cctv", cctv=True)
            print(save_as + "\t SUS: " + str("%.2f" % val) + "\t Copy to: " + location)
            logger.log('info', save_as + "\t SUS: " + str(val) + "\t Copy to: " + location)

            os.remove(att_path)

    def scan_mail(self, mb, scan_type, get_attach, delete):
        try:
            self.outlook.select(mailbox=mb, readonly=False)
            (result, messages) = self.outlook.search(None, scan_type)
        except imaplib.IMAP4.error:
            communicator.send_to_master("Connection Error - MB Select")
            print("Mailbox select error")
            self.connection_err = self.connection_err + 1
            return

        if result == "OK":
            email_count = len(messages[0].split(b' '))
            for i in range(email_count):
                message = "1"
                try:
                    ret, data = self.outlook.fetch(message, '(RFC822)')
                except imaplib.IMAP4.error:
                    print("No new emails to read.")
                    self.outlook.connection.close()
                    exit()

                if get_attach:
                    try:
                        msg = email.message_from_bytes(data[0][1])
                    except AttributeError:
                        print("No new messages")
                        logger.log('error', 'No new messages')
                        return

                    date = msg['Date']
                    date = date.replace(" +0530", "")

                    self.get_attachment(msg, date)

                if delete:
                    try:
                        self.outlook.store(message, '+FLAGS', '\\Deleted')
                        self.outlook.expunge()
                    except imaplib.IMAP4.error:
                        print("1 message skipped delete")
                        communicator.send_to_master("Connection Error - Delete")
                        logger.log('error', '1 message skipped delete')
                        self.connection_err = self.connection_err + 1
                        return

    def run_code(self):
        self.log_in()
        self.scan_mail('Security', 'UnSeen', True, True)

        try:
            self.outlook.close()
        except (imaplib.IMAP4.abort, imaplib.IMAP4.error):
            communicator.send_to_master("Connection Error - Close")
            print("Connection Error")
            self.connection_err = self.connection_err + 1

        print("-------CCTV-------")

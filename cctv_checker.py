import email
import imaplib
import os
import random
import global_var
import image_classifier
import settings
import communicator
import logger


class CCTVChecker:
    outlook = imaplib.IMAP4_SSL('outlook.office365.com', 993)
    last_t = 0
    occur_t = 0
    img = None

    def __int__(self):
        for f in os.listdir(settings.cctv_download):
            os.remove(os.path.join(settings.cctv_download, f))

    def log_in(self):
        try:
            self.outlook.login(settings.em, settings.pw)
        except imaplib.IMAP4.error:
            print("Logged In")

    def get_attachment(self, msg, date):
        att: int = 0
        for part in msg.walk():
            if part.get_content_maintype() == 'multipart':
                continue
            if part.get('Content-Disposition') is None:
                continue

            save_as = date + " " + part.get_filename()
            save_as = save_as.replace(",", "")
            save_as = save_as.replace(":", "-")
            att_path = os.path.join(settings.cctv_download, save_as)

            if not os.path.isfile(att_path):
                fp = open(att_path, 'wb')
                fp.write(part.get_payload(decode=True))
                fp.close()

            file_n = part.get_filename()
            val, sus = image_classifier.classify(file_n, att_path)
            if sus:
                if att == 0:
                    communicator.send_now(date, "cctv", cctv=True)
                    att = att + 1
                communicator.send_now(att_path, "cctv", img=True, cctv=True)
                communicator.send_now(str(val), "cctv", cctv=True)
            print(save_as + "\t SUS: " + str(val))

            if random.random() > 0.7:
                if "A01" in file_n:
                    sav = settings.cctv_save + "/A01"
                elif "A02" in file_n:
                    sav = settings.cctv_save + "/A02"
                else:
                    continue

                if sus:
                    sav = sav + "/1"
                else:
                    sav = sav + "/0"

                save_path = os.path.join(sav, save_as)
                fp = open(save_path, 'wb')
                fp.write(part.get_payload(decode=True))
                fp.close()

            logger.log('info', save_as)
            os.remove(att_path)

    def scan_mail(self, mb, scan_type, get_attach, delete):
        try:
            self.outlook.select(mailbox=mb, readonly=False)
            (result, messages) = self.outlook.search(None, scan_type)
        except imaplib.IMAP4.error:
            communicator.send_to_master("Connection Error - MB Select")
            print("Mailbox select error")
            global_var.connection_err = global_var.connection_err + 1
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
                        global_var.connection_err = global_var.connection_err + 1
                        return

    def run_code(self):
        try:
            self.log_in()
        except (imaplib.IMAP4.abort, imaplib.IMAP4.error):
            communicator.send_to_master("Connection Error - Login")
            print("Connection Error")
            global_var.connection_err = global_var.connection_err + 1

        self.scan_mail('Security', 'UnSeen', True, True)

        # try:
        #     self.outlook.close()
        # except (imaplib.IMAP4.abort, imaplib.IMAP4.error):
        #     communicator.send_to_master("Connection Error - Close")
        #     print("Connection Error")
        #     global_var.connection_err = global_var.connection_err + 1

        print("-------CCTV-------")

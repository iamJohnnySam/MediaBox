import email
import imaplib
import os
import shutil
import random
import global_var
import settings
import communicator
import logger


class CCTVChecker:
    outlook = imaplib.IMAP4_SSL('outlook.office365.com', 993)
    last_t = 0
    occur_t = 0
    photos = 3
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
            if att >= self.photos:
                continue
            att = att + 1

            save_as = date + " " + part.get_filename()
            save_as = save_as.replace(",", "")
            save_as = save_as.replace(":", "-")
            print(save_as)
            att_path = os.path.join(settings.cctv_download, save_as)

            if not os.path.isfile(att_path):
                fp = open(att_path, 'wb')
                fp.write(part.get_payload(decode=True))
                fp.close()

            if att == 1:
                communicator.send_now(date, "cctv", cctv=True)
            communicator.send_now(att_path, "cctv", img=True, cctv=True)
            if random.random() > 0.7:
                save_path = os.path.join(settings.cctv_save, save_as)
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

                    t_string = date[-8:]
                    t = int(t_string[0:2]) * 3600
                    t = t + int(t_string[3:5]) * 60
                    t = t + int(t_string[-2:])

                    if (t - self.last_t) <= 90:
                        self.occur_t = self.occur_t + 1
                        print(t, " | ", self.last_t, " | ", t - self.last_t, " | ", self.occur_t)
                    else:
                        self.occur_t = 0

                    self.last_t = t

                    if self.occur_t >= 5:
                        self.photos = 1
                        print("High frequency detected = 5")
                    elif self.occur_t >= 3:
                        self.photos = 2
                        print("High frequency detected = 3")
                    else:
                        self.photos = 3

                    self.get_attachment(msg, date)

                if delete:
                    try:
                        self.outlook.store(message, '+FLAGS', '\\Deleted')
                        self.outlook.expunge()
                    except imaplib.IMAP4.error:
                        print("1 message skipped delete")
                        logger.log('error', '1 message skipped delete')
                        global_var.connection_err = global_var.connection_err + 1
                        return

    def run_code(self):
        try:
            self.log_in()
            self.scan_mail('Security', 'UnSeen', True, True)
            self.outlook.close()
        except (imaplib.IMAP4.abort, imaplib.IMAP4.error):
            communicator.send_to_master("Connection Error")
            print("Connection Error")
            global_var.connection_err = global_var.connection_err + 1
        print("-------CCTV-------")

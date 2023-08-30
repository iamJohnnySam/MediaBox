import email
import imaplib
import os
import smtplib
import ssl
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate
from os.path import basename
import numpy as np
from PIL import Image, ImageOps
import settings
import communicator


class CCTVChecker:
    folderSize = 0
    output = 0.000001
    outlook = imaplib.IMAP4_SSL('outlook.office365.com', 993)

    def __int__(self):
        for f in os.listdir(settings.cctv_download):
            self.folderSize = self.folderSize + os.path.getsize(os.path.join(settings.cctv_download, f))
        print("Current Folder size -", "{:,}".format(self.folderSize))

    def log_in(self, mb):
        try:
            self.outlook.login(settings.em, settings.pw)
        except:
            pass
        self.outlook.select(mailbox=mb, readonly=False)

    def process_attach_image(self, path):
        img = Image.open(path)
        img = ImageOps.grayscale(img)
        img = np.asarray(img, dtype="float32") / 255
        img = np.expand_dims(img, axis=0)
        return img

    def get_attachment(self, msg, date):
        att_path = "No attachment found."
        for part in msg.walk():
            if part.get_content_maintype() == 'multipart':
                continue
            if part.get('Content-Disposition') is None:
                continue

            filename = part.get_filename()
            save_as = date + " " + filename
            save_as = save_as.replace(",", "")
            save_as = save_as.replace(":", "-")
            print(save_as)
            att_path = os.path.join(settings.cctv_download, save_as)

            if not os.path.isfile(att_path):
                fp = open(att_path, 'wb')
                fp.write(part.get_payload(decode=True))
                fp.close()

            # IMAGE
            img = self.process_attach_image(att_path)

            self.output = "no neural net"
            sus = True

            if sus:
                communicator.send_image(att_path)
                communicator.send_now("Sus lvl " + str(self.output))

            os.remove(att_path)

    def scan_mail(self, scan_type, get_attach, delete):
        (result, messages) = self.outlook.search(None, scan_type)

        if result == "OK":
            for message in messages[0].split(b' '):
                try:
                    ret, data = self.outlook.fetch(message, '(RFC822)')
                except:
                    print("No new emails to read.")
                    self.outlook.connection.close()
                    exit()

                if get_attach:
                    msg = email.message_from_bytes(data[0][1])
                    date = msg['Date']
                    date = date.replace(" +0530", "")

                    self.get_attachment(msg, date)

                if delete:
                    self.outlook.store(message, '+FLAGS', '\\Deleted')
                    self.outlook.expunge()

    def run_code(self):
        self.log_in('Security')
        self.scan_mail('UnSeen', True, True)
        self.outlook.close()

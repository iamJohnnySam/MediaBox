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
        except imaplib.IMAP4.error:
            pass
        self.outlook.select(mailbox=mb, readonly=False)

    def process_attach_image(self, path):
        img = Image.open(path)
        img = ImageOps.grayscale(img)
        img = np.asarray(img, dtype="float32") / 255
        img = np.expand_dims(img, axis=0)
        return img

    def get_attachment(self, data):
        msg = email.message_from_bytes(data[0][1])
        date = msg['Date']
        date = date.replace(" +0530", "")

        att_path = "No attachment found."
        for part in msg.walk():
            if part.get_content_maintype() == 'multipart':
                continue
            if part.get('Content-Disposition') is None:
                continue

            filename = part.get_filename()
            save_as = date + " " + filename
            att_path = os.path.join(settings.cctv_download, save_as)

            image = part.get_payload(decode=True)
            fp = open(att_path, 'wb')
            fp.write(image)
            fp.close()

            # IMAGE
            img = self.process_attach_image(att_path)

            sus = False
            self.output = "no neural net"
            sus = True

            if not sus:
                os.remove(att_path)

            else:
                settings.bot.sendPhoto(settings.telepot_chat, photo=open(att_path, 'rb'))
                settings.bot.sendMessage(settings.telepot_chat, "Sus lvl " + str(self.output))

            if sus:
                self.folderSize = self.folderSize + os.path.getsize(att_path)
                print(filename, self.output, "{:,}".format(self.folderSize))

    def scan_mail(self, scan_type, get_attach, delete):
        (result, messages) = self.outlook.search(None, scan_type)

        if result == "OK":
            for message in messages[0].split():
                try:
                    ret, data = self.outlook.fetch(message, '(RFC822)')
                except:
                    print("No new emails to read.")
                    self.outlook.connection.close()
                    exit()

                if get_attach:
                    self.get_attachment(data)

                if delete:
                    self.outlook.store(message, '+FLAGS', '\\Deleted')
                    self.outlook.expunge()

    def send_email(self, send_to, body):
        msg = MIMEMultipart()
        msg['From'] = settings.em
        msg['To'] = ", ".join(send_to)
        msg['Date'] = formatdate(localtime=True)
        msg['Subject'] = "Suspicious Activity"

        msg.attach(MIMEText(body, "html"))

        for f in os.listdir(settings.cctv_download):
            with open(os.path.join(settings.cctv_download, f), "rb") as fil:
                part = MIMEApplication(fil.read(), Name=basename(f))
            part['Content-Disposition'] = 'attachment; filename="%s"' % basename(f)
            msg.attach(part)

        context = ssl.create_default_context()
        server = smtplib.SMTP("smtp.office365.com", 587)
        server.starttls(context=context)
        server.login(settings.em, settings.pw)
        server.sendmail(settings.em, send_to, msg.as_string())
        server.close()

    def run_code(self):
        self.log_in('Security')
        self.scan_mail('UnSeen', True, True)
        self.outlook.close()

        if self.folderSize > 0:
            send_to = [settings.email1, settings.email2]
            body = """
                <html><body>
                    <p>Hi,<br>
                    We detected some activity on the CCTV in the last 24 hours<br></p>
                </body> </html>
            """

            self.send_email(send_to, body)

            for f in os.listdir(settings.cctv_download):
                os.remove(os.path.join(settings.cctv_download, f))
            self.folderSize = 0

        print("Done")

    def clear_sent(self):
        self.log_in('Sent')
        self.scan_mail('ALL', False, True)
        self.outlook.close()
        self.outlook.logout()
        print("Done")

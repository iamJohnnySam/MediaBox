import email
import imaplib
import os
import settings
import communicator
import logger


class CCTVChecker:
    outlook = imaplib.IMAP4_SSL('outlook.office365.com', 993)

    def __int__(self):
        for f in os.listdir(settings.cctv_download):
            os.remove(os.path.join(settings.cctv_download, f))

    def log_in(self):
        try:
            self.outlook.login(settings.em, settings.pw)
        except:
            print("Logged In")

    def get_attachment(self, msg, date):
        att = 0
        att_path = "No attachment found."
        for part in msg.walk() and att < 2:
            att = att + 1
            if part.get_content_maintype() == 'multipart':
                continue
            if part.get('Content-Disposition') is None:
                continue

            save_as = date + " " + part.get_filename()
            save_as = save_as.replace(",", "")
            save_as = save_as.replace(":", "-")
            print(save_as)
            att_path = os.path.join(settings.cctv_download, save_as)

            if not os.path.isfile(att_path):
                fp = open(att_path, 'wb')
                fp.write(part.get_payload(decode=True))
                fp.close()

            communicator.send_image(att_path)
            communicator.send_now(save_as)
            logger.log('info', save_as)

            os.remove(att_path)

    def scan_mail(self, mb, scan_type, get_attach, delete):
        self.outlook.select(mailbox=mb, readonly=False)
        (result, messages) = self.outlook.search(None, scan_type)

        if result == "OK":
            email_count = len(messages[0].split(b' '))
            for i in range(email_count):
                message = b'1'
                try:
                    ret, data = self.outlook.fetch(message, '(RFC822)')
                except:
                    print("No new emails to read.")
                    self.outlook.connection.close()
                    exit()

                if get_attach:
                    try:
                        msg = email.message_from_bytes(data[0][1])
                        date = msg['Date']
                        date = date.replace(" +0530", "")

                        self.get_attachment(msg, date)
                    except:
                        print("Message Skipped")
                        logger.log('error', '1 message skipped')

                if delete:
                    try:
                        self.outlook.store(message, '+FLAGS', '\\Deleted')
                        self.outlook.expunge()
                    except:
                        print("1 message skipped delete")
                        logger.log('error', '1 message skipped delete')

    def run_code(self):
        self.log_in()
        try:
            self.scan_mail('Security', 'UnSeen', True, True)
        except:
            print("Mail box select error")
            logger.log('error', 'Mail box select error')
        self.outlook.close()

import email
import imaplib
import logger
from communication import communicator


class EmailManager:
    result = "Not OK"
    attachments = {}

    def __init__(self, email_address, password, mb):
        self.msg = None
        self.current_date = None
        self.current_message = "1"
        self.unread_emails = 0
        self.connection_err = 0
        self.email = email_address
        self.password = password
        self.mb = mb
        self.myEmail = imaplib.IMAP4_SSL('outlook.office365.com', 993)

    def log_in(self):
        try:
            self.myEmail.login(self.email, self.password)
        except imaplib.IMAP4.error:
            print("Logged In")

    def select_mailbox(self):
        try:
            self.myEmail.select(mailbox=self.mb, readonly=False)
            return True
        except imaplib.IMAP4.error:
            print("Mailbox select error")
            self.connection_err = self.connection_err + 1
            return False

    def check_email(self, scan_type='UnSeen'):
        try:
            (self.result, self.messages) = self.myEmail.search(None, scan_type)
            self.unread_emails = len(self.messages[0].split(b' '))
            return True, self.unread_emails
        except imaplib.IMAP4.error:
            print("Mailbox search error")
            return False

    def connect(self):
        self.log_in()
        b = self.select_mailbox()
        c = self.check_email()

        if not (b and c):
            self.result = "Not OK"

    def email_close(self):
        self.myEmail.connection.close()

    def get_next_message(self, message="1"):
        self.current_message = message

        if self.result != "OK":
            self.connect()

        if self.result == "OK":
            try:
                ret, data = self.myEmail.fetch(message, '(RFC822)')
            except imaplib.IMAP4.error:
                print("No new emails to read.")
                self.email_close()
                return False

            self.msg = email.message_from_bytes(data[0][1])
            self.current_date = self.msg['Date']
            self.current_date = self.current_date.replace(" +0530", "")
            return True

    def delete_email(self):
        try:
            self.myEmail.store(self.current_message, '+FLAGS', '\\Deleted')
            self.myEmail.expunge()
        except imaplib.IMAP4.error:
            print("1 message skipped delete")
            communicator.send_to_master("Connection Error - Delete")
            logger.log('error', '1 message skipped delete')
            self.connection_err = self.connection_err + 1

    def get_next_attachment(self):
        self.connect()

        if len(self.attachments.keys()) == 0:
            if self.unread_emails > 0:
                self.delete_email()
                worked = self.get_next_message()
                if not worked:
                    return False, None, None, None
                self.unread_emails = self.unread_emails - 1
                attachments = self.msg.walk()
                for part in attachments:
                    if part.get_content_maintype() == 'multipart' or part.get('Content-Disposition') is None:
                        continue
                    else:
                        self.attachments[part.get_filename()] = part.get_payload(decode=True)
            else:
                return False, None, None, None


        file_n = list(self.attachments.keys())[0]
        attachment = self.attachments[file_n]
        del self.attachments[file_n]

        return True, attachment, self.current_date, file_n

import email
import imaplib
import logger
from communication import communicator


class EmailManager:
    result = "Not OK"
    attachments = {}
    current_date = None
    current_message = "1"

    def __init__(self, email_address, password, mb):
        self.msg = None
        self.unread_emails = 0
        self.connection_err = 0
        self.email = email_address
        self.password = password
        self.mb = mb
        self.myEmail = imaplib.IMAP4_SSL('outlook.office365.com', 993)
        logger.log("Email Manager Object Created - " + email_address)

    def log_in(self):
        try:
            self.myEmail.login(self.email, self.password)
        except imaplib.IMAP4.error:
            pass

    def select_mailbox(self, mailbox=None):
        if mailbox is None:
            mailbox = self.mb
        try:
            self.myEmail.select(mailbox=mailbox, readonly=False)
            return True
        except imaplib.IMAP4.error:
            logger.log("Mailbox select error", source="EM", message_type="error")
            self.connection_err = self.connection_err + 1
            return False

    def check_email(self, scan_type='UnSeen'):
        try:
            (self.result, self.messages) = self.myEmail.search(None, scan_type)
            self.unread_emails = len(self.messages[0].split(b' '))
            return True, self.unread_emails
        except imaplib.IMAP4.error:
            logger.log("Mailbox search error", source="EM", message_type="error")
            return False

    def connect(self, mailbox=None):
        self.log_in()
        b = self.select_mailbox(mailbox)
        c = self.check_email()

        if not (b and c):
            self.result = "Not OK"
            logger.log("Email Error", source="EM", message_type="error")

    def email_close(self):
        self.myEmail.close()

    def get_next_message(self, message="1"):
        self.current_message = message

        if self.result != "OK":
            self.connect()

        if self.result == "OK":
            ret, data = self.myEmail.fetch(message, '(RFC822)')

            try:
                self.msg = email.message_from_bytes(data[0][1])
            except AttributeError:
                logger.log("No new emails to read.", source="EM")
                self.email_close()
                return False

            self.current_date = self.msg['Date']
            self.current_date = self.current_date.replace(" +0530", "")
            return True

    def delete_current_email(self):
        try:
            self.myEmail.store(self.current_message, '+FLAGS', '\\Deleted')
            self.myEmail.expunge()
        except imaplib.IMAP4.error:
            logger.log("1 message skipped delete", source="EM", message_type="warn")
            communicator.send_to_master("cctv", "Connection Error - Delete")
            self.connection_err = self.connection_err + 1

    def delete_all_emails(self, mailbox="Sent"):
        message = "1"

        self.connect(mailbox)

        exit_condition = True
        count = 0
        while exit_condition:
            try:
                self.myEmail.store(message, '+FLAGS', '\\Deleted')
                self.myEmail.expunge()
                count = count + 1
                logger.log("Deleted Email", source="EM")
            except AttributeError:
                exit_condition = False
                logger.log("No new emails to delete.", source="EM")
                self.email_close()
                logger.log("Deleted " + count + "emails from " + self.mb, source="EM")
                communicator.send_to_master("main", "Deleted " + count + "emails from " + self.mb)
                return

    def get_next_attachment(self):
        self.connect()

        if len(self.attachments.keys()) == 0:
            if self.unread_emails > 0:
                self.delete_current_email()
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

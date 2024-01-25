import email
import imaplib
import traceback

import global_var
import logger


class EmailManager:
    result = "Not OK"
    attachments = {}
    current_date = None
    current_message = "1"

    def __init__(self, email_address, password, mb):
        self.mail_connect_error = False
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
        except imaplib.IMAP4.error as err:
            logger.log(f"Mailbox login error - {str(err)}", message_type="debug")
            logger.log(traceback.format_exc(), message_type="debug")

    def select_mailbox(self, mailbox=None):
        if mailbox is None:
            mailbox = self.mb
        try:
            self.myEmail.select(mailbox=mailbox, readonly=False)
            return True
        except imaplib.IMAP4.error as err:
            logger.log(f"Mailbox select error - {str(err)}", message_type="error")
            logger.log(traceback.format_exc(), message_type="debug")
            self.connection_err = self.connection_err + 1
            return False

    def check_email(self, scan_type='UnSeen'):
        try:
            (self.result, self.messages) = self.myEmail.search(None, scan_type)
            self.unread_emails = len(self.messages[0].split(b' '))
            return True, self.unread_emails
        except imaplib.IMAP4.error as err:
            logger.log(f"Mailbox search error - {str(err)}", message_type="error")
            logger.log(traceback.format_exc(), message_type="debug")
            return False

    def connect(self, mailbox=None):
        self.log_in()
        b = self.select_mailbox(mailbox)
        c = self.check_email()

        if not (b and c):
            self.result = "Not OK"
            logger.log("Email Error", message_type="error")
            self.mail_connect_error = True

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
                logger.log("No new emails to read.")
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
            logger.log("1 message skipped delete", message_type="warn")
            self.connection_err = self.connection_err + 1

    def delete_all_emails(self, mailbox="Sent"):
        logger.log("-------STARTED EMAIL CLEAN-UP SCRIPT-------")
        message = "1"

        self.connect(mailbox)

        if self.connection_err > 0:
            exit_condition = False
        else:
            exit_condition = True

        count = 0
        while exit_condition and (not global_var.stop_all):
            try:
                ret, data = self.myEmail.fetch(message, '(RFC822)')
            except (imaplib.IMAP4.error, imaplib.IMAP4.abort) as error:
                exit_condition = False
                self.connection_err = self.connection_err + 1
                logger.log("Error Occurred: " + str(error))
                return
            try:
                self.msg = email.message_from_bytes(data[0][1])
            except AttributeError:
                exit_condition = False
                logger.log("No new emails to delete.")
                self.email_close()
                logger.log("Deleted " + str(count) + " emails from " + self.mb)
                logger.log("-------ENDED EMAIL CLEAN-UP SCRIPT-------")
                return
            try:
                self.myEmail.store(message, '+FLAGS', '\\Deleted')
                self.myEmail.expunge()
                count = count + 1
                logger.log("Deleted Email - " + self.msg['Date'])
            except AttributeError:
                logger.log("Failed to delete - " + self.msg['Date'])

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

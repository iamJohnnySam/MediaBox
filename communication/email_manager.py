import email
import imaplib
import traceback

import global_variables
from brains.job import Job
from tools.logger import log


class EmailManager:
    def __init__(self, job: Job, email_address, imap, password, mb):
        self.result = "Not OK"
        self.attachments = {}
        self.current_date = None
        self.current_message = "1"

        self.job = job
        self.mail_connect_error = False
        self.msg = None
        self.unread_emails = 0
        self.connection_err = 0
        self.email = email_address
        self.password = password
        self.mb = mb
        self.myEmail = imaplib.IMAP4_SSL(imap, 993)
        log(self.job.job_id, "Email Manager Object Created - " + email_address)

    def log_in(self):
        log(self.job.job_id, f"Current state: {self.myEmail.state}")
        if self.myEmail.state == "NONAUTH":
            try:
                self.myEmail.login(self.email, self.password)
                log(self.job.job_id, "Login Success")
            except imaplib.IMAP4.error as err:
                log(self.job.job_id, str(err), error_code=10004)
                log(self.job.job_id, traceback.format_exc(), log_type="debug")
                log(self.job.job_id, f"Current state: {self.myEmail.state}")
                raise imaplib.IMAP4.error
            log(self.job.job_id, f"Current state: {self.myEmail.state}")
        return True

    def select_mailbox(self, mailbox=None):
        if mailbox is None:
            mailbox = self.mb
        try:
            self.myEmail.select(mailbox=mailbox, readonly=False)
        except imaplib.IMAP4.error as err:
            log(self.job.job_id, f"Mailbox select error - {str(err)}", log_type="error")
            log(self.job.job_id, traceback.format_exc(), log_type="debug")
            self.connection_err = self.connection_err + 1
            return False

        if self.myEmail.state == "SELECTED":
            log(self.job.job_id, f"Mailbox Select Success: {mailbox}")
            return True
        else:
            return False

    def check_email(self, scan_type='UnSeen'):
        try:
            (self.result, self.messages) = self.myEmail.search(None, scan_type)
            self.unread_emails = len(self.messages[0].split(b' '))
            log(self.job.job_id, "Check Mail Success")
            return True, self.unread_emails
        except imaplib.IMAP4.error as err:
            log(self.job.job_id, f"Mailbox search error - {str(err)}", log_type="error")
            log(self.job.job_id, traceback.format_exc(), log_type="debug")
            return False

    def connect(self, mailbox=None):
        a = self.log_in()
        if not a:
            self.result = "Not OK"
            log(self.job.job_id, "Login Error", log_type="error")
            self.mail_connect_error = True
            return
        log(self.job.job_id, f"Current state: {self.myEmail.state}")
        b = self.select_mailbox(mailbox)
        log(self.job.job_id, f"Current state: {self.myEmail.state}")
        c = self.check_email()

        if not (b and c):
            self.result = "Not OK"
            log(self.job.job_id, "Email Error", log_type="error")
            self.mail_connect_error = True

    def email_close(self):
        log(self.job.job_id, f"Current state: {self.myEmail.state}")
        if self.myEmail.state == "SELECTED":
            self.myEmail.close()
            log(self.job.job_id, f"Current state: {self.myEmail.state}")
        if self.myEmail.state == "AUTH":
            self.myEmail.logout()
            log(self.job.job_id, f"Current state: {self.myEmail.state}")

    def get_next_message(self, message="1"):
        self.current_message = message

        if self.result != "OK":
            self.connect()

        if self.result == "OK":
            ret, data = self.myEmail.fetch(message, '(RFC822)')

            try:
                self.msg = email.message_from_bytes(data[0][1])
            except (AttributeError, TypeError):
                log(self.job.job_id, "No new emails to read.")
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
            log(self.job.job_id, "1 message skipped delete", log_type="warn")
            self.connection_err = self.connection_err + 1

    def delete_all_emails(self, mailbox="Sent"):
        log(self.job.job_id, "-------STARTED EMAIL CLEAN-UP SCRIPT-------")
        message = "1"

        self.connect(mailbox)

        if self.connection_err > 0:
            exit_condition = False
        else:
            exit_condition = True

        count = 0
        while exit_condition and (not global_variables.stop_all):
            try:
                ret, data = self.myEmail.fetch(message, '(RFC822)')
            except (imaplib.IMAP4.error, imaplib.IMAP4.abort) as error:
                self.connection_err = self.connection_err + 1
                log(self.job.job_id, "Error Occurred: " + str(error))
                return
            try:
                self.msg = email.message_from_bytes(data[0][1])
            except (AttributeError, TypeError):
                log(self.job.job_id, "No new emails to delete.")
                self.email_close()
                log(self.job.job_id, "Deleted " + str(count) + " emails from " + self.mb)
                log(self.job.job_id, "-------ENDED EMAIL CLEAN-UP SCRIPT-------")
                return
            try:
                self.myEmail.store(message, '+FLAGS', '\\Deleted')
                self.myEmail.expunge()
                count = count + 1
                log(self.job.job_id, "Deleted Email - " + self.msg['Date'])
            except AttributeError:
                log(self.job.job_id, "Failed to delete - " + self.msg['Date'])

    def get_next_attachment(self):
        if self.myEmail.state != "SELECTED":
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

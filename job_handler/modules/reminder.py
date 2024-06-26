from shared_models.job import Job
from shared_models.message import Message
from job_handler.base_module import Module
from shared_tools import word_tools


# todo


class Reminder(Module):
    def __init__(self, job: Job):
        super().__init__(job)

    def read_news(self):
        greeting = word_tools.greeting()
        message = f"{greeting} {self.job.username}, Can I get the news for you?"
        send_message = Message(message, job=self.job)
        send_message.keyboard_extractor(function=['check_news_all', 'check_news'],
                                        options=['', ''],
                                        button_text=['Read all', 'Show Channels'])
        self.send_message(send_message)

    # todo check last 5/10 messages to see if a similar message has been sent

    # todo create job as reminder complete. Example Invest. If done how much invested and where to be added.

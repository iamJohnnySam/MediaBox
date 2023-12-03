from openai import OpenAI
from communication import communicator
import logger
import settings


class TalkToAI:
    telepot_account = "main"

    def __init__(self, chat):
        self.client = OpenAI(api_key=settings.chat)

        self.chat_id = chat
        self.messages = [{"role": "system",
                          "content": "You are a intelligent assistant."}]

        logger.log("OpenAI Object Created for " + chat)

    def send_to_ai(self, message):
        self.messages.append({"role": "user", "content": message})
        chatgpt = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=self.messages
        )

        reply = str(chatgpt.choices[0].message.content)
        self.messages.append({"role": "assistant", "content": reply})
        communicator.send_message(self.telepot_account, self.chat_id, reply)
        logger.log(str(reply), source="AI")

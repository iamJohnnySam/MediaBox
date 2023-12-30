from datetime import datetime

import telepot
from telepot.loop import MessageLoop
from telepot.namedtuple import InlineKeyboardButton, InlineKeyboardMarkup

import logger
from database_manager.json_editor import JSONEditor


class CommunicatorBase:
    source = "TG-B"

    def __init__(self, telepot_account):
        self.current_callback_id = 0
        self.callback_id_prefix = telepot_account + "_" + datetime.now().strftime("%y%m%d%H%M") + "_"

        self.allowed_chats = {}
        self.telepot_groups = {}
        self.telepot_account = telepot_account

        telepot_accounts = JSONEditor('communication/telepot_accounts.json').read()
        self.bot = telepot.Bot(telepot_accounts[telepot_account]["account"])
        self.master = telepot_accounts[telepot_account]["master"]

        self.telepot_chat_id = JSONEditor('communication/telepot_groups.json')
        self.command_dictionary = JSONEditor('communication/commands/telepot_commands_' +
                                             self.telepot_account + '.json').read()

        MessageLoop(self.bot, {'chat': self.handle,
                               'callback_query': self.handle_callback}).run_as_thread()
        logger.log('Telepot ' + telepot_account + ' listening', source=self.source)

    def send_to_group(self, group, msg, image=False, caption=""):
        if self.telepot_groups == {} or self.telepot_groups is None:
            self.telepot_groups = self.telepot_chat_id.read()

        chats = self.telepot_groups[group]

        logger.log(str(chats) + " - Group Message: " + msg, self.source)

        for chat in chats:
            if image:
                self.bot.sendPhoto(chat, photo=open(msg, 'rb'), caption=caption)
            else:
                self.bot.sendMessage(chat, msg)

    def send_now(self, msg, image=False, chat=None, keyboard=None, reply_to=None, caption=""):
        if msg == "" or msg is None:
            logger.log("NO MESSAGE", source=self.source, message_type="error")
            return

        if chat is None:
            chat = self.master

        if image:
            message = self.bot.sendPhoto(chat, photo=open(msg, 'rb'), reply_to_message_id=reply_to, caption=caption)
        elif keyboard is not None:
            self.current_callback_id = self.current_callback_id + 1
            message = self.bot.sendMessage(chat, msg, reply_markup=keyboard, reply_to_message_id=reply_to)
        else:
            message = self.bot.sendMessage(chat, msg, reply_to_message_id=reply_to)

        logger.log(str(chat) + " - " + str(message['message_id']) + " - Message: " + msg, self.source)

        return message

    def keyboard_button(self, text, callback_command, value="None"):
        # FORMAT
        # Full   = Account _ %y%m%d%H%M _ CB-ID _ buttonText , DATA
        # DATA   = functionCall, Value

        data_id = self.callback_id_prefix + str(self.current_callback_id) + "_" + text
        data = data_id + "," + str(callback_command).lower() + "," + str(value)

        if len(data) >= 60:
            telepot_callbacks = {data_id: str(callback_command) + "," + str(value)}
            JSONEditor('database/telepot/' +
                       self.callback_id_prefix + 'telepot_callback_database.json').add_level1(telepot_callbacks)
            data = data_id + ",X"

        return data_id, InlineKeyboardButton(text=str(text), callback_data=data)

    def link_msg_to_buttons(self, message, buttons):
        for button in buttons:
            button_dict = {button: message}
            JSONEditor('database/telepot/' +
                       self.callback_id_prefix + 'telepot_button_link.json').add_level1(button_dict)

    def check_allowed_sender(self, chat_id, msg):
        # Load allowed list of chats first time
        sender_name = str(msg['chat']['first_name'])

        if self.allowed_chats is None or self.allowed_chats == {}:
            self.allowed_chats = JSONEditor('communication/telepot_allowed_chats.json').read().keys()

        if str(chat_id) in self.allowed_chats:
            return True
        else:
            self.bot.sendMessage(chat_id,
                                 "Hello " + sender_name + "! You're not allowed to be here")
            self.send_now("Unauthorised Chat access: " + sender_name)
            logger.log("Unauthorised Chat access: " + sender_name, source=self.source,
                       message_type="warn")
            return False

    def handle(self, msg):
        chat_id = msg['chat']['id']
        message_id = msg['message_id']

        if 'text' in msg.keys():
            self.handle_text(msg, chat_id, message_id)
        elif 'photo' in msg.keys():
            self.handle_photo(msg, chat_id, message_id)
        else:
            logger.log("Unknown Chat type", source=self.source, message_type="error")

    def handle_text(self, msg, chat_id, message_id):
        try:
            command = str(msg['text']).split(" ")[0]
        except KeyError:
            logger.log('Telepot Key Error: ' + str(msg), source=self.source, message_type="error")
            return

        logger.log(str(self.telepot_account) + "\t" + str(chat_id) + " - " + str(command), source=self.source)

        # Check if sender is in allowed list
        if self.check_allowed_sender(chat_id, msg):

            # If command is in command list
            if command in self.command_dictionary.keys():
                function = self.command_dictionary[command]["function"]
                logger.log(str(chat_id) + ' - Calling Function: ' + function, source=self.source)
                value = str(msg['text']).replace(str(msg['text']).split(" ")[0], "").strip()

                func = getattr(self, function)
                func(msg, chat_id, message_id, value)

            elif command == '/help' or command.lower() == 'help' or command == "/start":
                message = "--- AVAILABLE COMMANDS ---"
                for commands in self.command_dictionary.keys():
                    message = message + "\n" + commands + " - " + self.command_dictionary[commands]["definition"]

                self.send_now(message,
                              image=False,
                              chat=chat_id)

            elif "/" in command:
                self.send_now("Sorry, that command is not known to me...",
                              image=False,
                              chat=chat_id)
            else:
                # self.send_now(Bard().get_answer(msg)['content']
                self.send_now("Chatbot Disabled. Type /help to find more information",
                              image=False,
                              chat=chat_id)

    def handle_photo(self, msg, chat_id, message_id):
        pass

    def handle_callback(self, msg):
        query_id, from_id, query_data = telepot.glance(msg, flavor='callback_query')
        logger.log('Callback Query: ' + " " + str(query_id) + " " + str(from_id) + " " + str(query_data), self.source)

        callback_id = str(query_data).split(",")[0]
        command = str(query_data).split(",")[1]

        if command == "X":
            comm = callback_id.split("_")[0] + "_" + callback_id.split("_")[1] + "_"
            telepot_callbacks = JSONEditor('database/telepot/'
                                           + comm + 'telepot_callback_database.json').read()

            query_data = telepot_callbacks[callback_id]
            logger.log("Recovered Query: " + query_data, self.source)

            command = str(query_data).split(",")[0]
            value = str(query_data).split(",")[1]

        else:
            value = str(query_data).split(",")[2]

        try:
            logger.log("Calling function: cb_" + command)
            func = getattr(self, "cb_" + command)
            func(callback_id, query_id, from_id, value)
        except (ValueError, SyntaxError) as error:
            self.bot.answerCallbackQuery(query_id, text='Unhandled')
            logger.log("Unhandled Callback: " + error, source=self.source, message_type="error")

    def update_in_line_buttons(self, button_id, keyboard=None):
        comm = button_id.split("_")[0] + "_" + button_id.split("_")[1] + "_"
        message = JSONEditor('database/telepot/' + comm + 'telepot_button_link.json').read()[button_id]
        logger.log("Buttons to remove from message id " + str(message['message_id']), self.source)
        message_id = telepot.message_identifier(message)
        self.bot.editMessageReplyMarkup(message_id, reply_markup=keyboard)

    def send_message_with_keyboard(self, msg, chat_id, button_text, button_cb, button_val,
                                   arrangement, reply_to=None):
        if len(button_text) == 0 or len(button_text) != len(button_cb) or len(button_text) != len(button_val):
            logger.log("Keyboard Generation error: " + str(msg), source=self.source, message_type="error")
            return

        button_ids = []
        buttons = []

        for i in range(len(button_text)):
            key_id, key_button = self.keyboard_button(button_text[i], button_cb[i], button_val[i])
            buttons.append(key_button)
            button_ids.append(key_id)

        keyboard_markup = []
        c = 0

        for i in range(len(arrangement)):
            keyboard_row = []
            for j in range(arrangement[i]):
                keyboard_row.append(buttons[c])
                c = c+1
            keyboard_markup.append(keyboard_row)

        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_markup)

        message = self.send_now(msg, chat=chat_id, keyboard=keyboard,
                                reply_to=reply_to)

        self.link_msg_to_buttons(message, button_ids)






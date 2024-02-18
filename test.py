def link_msg_to_buttons(self, message, buttons):
    for button in buttons:
        button_dict = {button: message}
        JSONEditor(global_var.telepot_callback_database +
                   self.callback_id_prefix + 'telepot_button_link.json').add_level1(button_dict)


def manage_chat_group(self, group, chat_id, add=True, remove=False):
    message_type = "info"
    where = f"chat_id = '{chat_id}' AND group_name = '{group}';"
    if not add ^ remove:
        msg = "Invalid command"
        message_type = "error"
    elif add and sql_databases["administration"].exists(self.database_groups, where) == 0:
        cols = "chat_id, group_name"
        vals = (chat_id, group)
        sql_databases["administration"].insert(self.database_groups, cols, vals)
        msg = f"Added {chat_id} to {group} group"
    elif remove and sql_databases["administration"].exists(self.database_groups, where) != 0:
        sql_databases["administration"].run_sql(f"DELETE FROM {self.database_groups} WHERE " + where)
        msg = f"Removed {chat_id} from {group} group"
    else:
        msg = "Nothing to do"

    logger.log(msg, message_type)
    return msg


def quick_cb(self, query: dict, command: str, value: str):
    reply_to = query['inline_message_id']
    chat = query['from']['id']

    if command == "echo":
        self.send_now(send_string=value, reply_to=reply_to, chat=chat)

    elif command == "torrent":
        success, torrent_id = transmission.download(value)
        if success:
            self.bot.editMessageReplyMarkup(reply_to, reply_markup=None)
            self.send_now("Movie will be added to queue", reply_to=reply_to, chat=chat)

    elif command == "cancel":
        self.bot.editMessageReplyMarkup(reply_to, reply_markup=None)

    self.bot.answerCallbackQuery(query['id'], text='Handled')


def todo(self):
    # todo

    query_id, from_id, query_data = telepot.glance(query, flavor='callback_query')

    if str(from_id) in self.waiting_user_input.keys():
        logger.log("Unable to continue. Waiting user input.")
        return

    callback_id = str(query_data).split(",")[0]
    command = str(query_data).split(",")[1]

    if command == "X":
        comm = callback_id.split("_")[0] + "_" + callback_id.split("_")[1] + "_"
        telepot_callbacks = JSONEditor(global_var.telepot_callback_database
                                       + comm + 'telepot_callback_database.json').read()

        query_data = telepot_callbacks[callback_id]
        logger.log("Recovered Query: " + query_data)

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
        logger.log("Unhandled Callback: " + str(error), log_type="error")


def update_in_line_buttons(self, button_id, keyboard=None):
    comm = button_id.split("_")[0] + "_" + button_id.split("_")[1] + "_"
    message = JSONEditor(global_var.telepot_callback_database
                         + comm + 'telepot_button_link.json').read()[button_id]
    logger.log("Buttons to remove from message id " + str(message['message_id']))
    message_id = telepot.message_identifier(message)
    self.bot.editMessageReplyMarkup(message_id, reply_markup=keyboard)
    return message['message_id']


def keyboard_extractor(self, identifier, num, result, cb, bpr=3, sql_result=True, command_only=False):
    if sql_result:
        button_text = [row[0] for row in result]
    else:
        button_text = result
    button_cb = [cb] * len(button_text)
    button_value = []
    for text in button_text:
        if command_only:
            button_value.append(f'{identifier};{text}')
        else:
            button_value.append(f'{identifier};{num};{text}')
    arrangement = [bpr for _ in range(int(math.floor(len(button_text) / 3)))]
    if len(button_text) % bpr != 0:
        arrangement.append(len(button_text) % 3)
    logger.log("Keyboard extracted > " + str(arrangement))

    return button_text, button_cb, button_value, arrangement


def get_user_input(self, user_id, callback, argument):
    self.waiting_user_input[user_id] = {"callback": callback,
                                        "argument": argument}


def received_user_input(self, msg):
    cb = self.waiting_user_input[msg.chat_id]["callback"]
    arg = self.waiting_user_input[msg.chat_id]["argument"]
    del self.waiting_user_input[msg.chat_id]

    message = str(msg['text'])

    logger.log(f'Calling function: {cb} with arguments {arg} and {message}.')
    func = getattr(self, cb)
    if "cb_" in cb:
        func(None, msg.message_id, msg.chat_id, message)
    else:
        func(msg, user_input=True, identifier=arg)


def check_command_value(self, msg: Message, index: int = 0, replace: str = "", inquiry: str = "",
                        check_int: bool = False,
                        check_float: bool = False):
    current_frame = inspect.currentframe()
    call_frame = inspect.getouterframes(current_frame, 2)

    if msg.check_value(index=index, replace_str=replace, check_int=check_int, check_float=check_float):
        return True
    else:
        if inquiry != "":
            send_string = f'Please send the {inquiry}.'
        elif replace != "":
            send_string = f'Please send the amount in {replace}.'
        else:
            send_string = f'Please send the value.'

        self.send_now(send_string, chat=msg.chat_id, reply_to=msg.message_id)
        self.get_user_input(msg.chat_id, call_frame[1][3], None)
        return False

    # MAIN FUNCTIONS


def save_photo(self, callback_id, query_id, from_id, value):
    message_id = self.update_in_line_buttons(callback_id)
    self.bot.answerCallbackQuery(query_id, text='Image will be saved')

    logger.log("Image saved as " + value)
    self.send_now("Image saved as " + value,
                  image=False,
                  chat=from_id,
                  reply_to=message_id)


def cb_cancel(self, callback_id, query_id, from_id, value):
    self.update_in_line_buttons(callback_id)
    self.bot.answerCallbackQuery(query_id, text='Canceled')


def cb_echo(self, callback_id, query_id, from_id, value):
    self.send_now(value, chat=from_id)
    self.bot.answerCallbackQuery(query_id, text='Sent')


def cb_run_command(self, callback_id, query_id, from_id, value):
    result = value.split(';')
    logger.log("Calling function: " + result[1])
    func = getattr(self, result[1])
    func(callback_id, query_id, from_id, result[0])


if 'steps' in self.command_dictionary[msg.command].keys():
    msg.steps = self.command_dictionary[msg.command]['steps']
if 'database' in self.command_dictionary[msg.command].keys():
    msg.database = self.command_dictionary[msg.command]['database']


from shared_models import configuration
from shared_tools.json_editor import JSONEditor
from shared_tools.logger import log


def extract_job_from_string(msg: str) -> (str, list):
    first_word: str = msg.split(" ")[0].lower()
    collection = []

    if first_word.startswith("/"):
        function = first_word.replace("/", "")

        if function == "start":
            function = "help"

        value = msg.replace(first_word, "").strip()
        if value != "":
            collection = value.split(" ")

    else:
        words = len(msg.split(" "))
        if first_word in ['cancel'] and words == 1:
            function = 'cancel'
        elif first_word in ['help', 'hi', 'hello'] and words == 1:
            function = 'help'
        else:
            function = "no_function"
        value = msg
        collection = [value]

    return function, collection


def extract_job_from_message(msg: dict) -> (str, int, str, int, list):
    chat_id = msg['chat']['id']
    reply_to = msg['message_id']
    username = msg['chat']['first_name']

    function: str = "no_function"
    collection: list = []

    photo_available = False

    if 'photo' in msg.keys():
        function = "photo"
        photo_available = True
        for pic in msg['photo']:
            collection.append(msg['photo'][pic]['file_id'])

    if 'text' in msg.keys():
        content = msg['text']
        function, _collection = extract_job_from_string(content)

        if _collection:
            collection = _collection

    else:
        log(error_code=20001)

    log(msg=f"Function: {function}, Collection: {collection}")

    return function, chat_id, username, reply_to, collection, photo_available


def create_keyboard_data(msg_id, reply_to, function, button_text, button_value, collection) -> str:
    if reply_to is None:
        reply_to = 0

    # FORMAT = msg_id; reply; btn_text; (function; step; value; collection)

    button_prefix = f"{msg_id};{reply_to};{button_text}"
    button_data = f"{button_prefix};{function};{button_value}"
    if collection != "":
        button_data = f"{button_data};{collection}"

    if len(button_data) >= 60:
        telepot_cb = {button_prefix: button_data}
        save_loc = configuration.Configuration().telegram["callback_overflow"]
        JSONEditor(save_loc).add_level1(telepot_cb, job_id=msg_id)
        log(job_id=msg_id, msg=f'Keyboard button saved > {telepot_cb}')
        button_data = f"{button_prefix};X"

    return button_data


def extract_job_from_callback(msg: dict):
    try:
        q = str(msg['data']).split(";")
    except ValueError as e:
        log(error_code=20002, error=str(e))
        return

    chat_id = msg['from']['id']
    username = msg['from']['first_name']

    # FORMAT = msg_id; reply; btn_text; (function; step; value; collection)

    if (not (len(q) == 4 and q[3] == 'X')) and (len(q) < 6):
        log(error_code=20003, msg=f"Not enough parameters in callback > {q}")
        return

    msg_id = q[0]
    if msg_id == "0":
        log(job_id=0, error_code=20004)
        return
    reply_to = q[1]

    msg_prefix = f"{q[0]};{q[1]};{q[2]}"

    if len(q) == 4 and q[3] == 'X':
        cb_file = JSONEditor(configuration.Configuration().telegram["callback_overflow"])
        query_data = cb_file.read()[msg_prefix]
        cb_file.delete(job_id=msg_id, key=msg_prefix)
        log(job_id=msg_id, msg="Recovered Query: " + query_data)

        try:
            q = str(query_data).split(";")
        except ValueError as e:
            log(job_id=msg_id, error_code=20003, error=str(e))
            return

    function = q[3]
    index = int(q[4])
    value = q[5]
    if len(q) > 5:
        collection = q[6:]
    else:
        collection = []

    return function, chat_id, username, reply_to, collection, index, value

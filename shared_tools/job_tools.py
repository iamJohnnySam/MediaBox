from shared_tools.logger import log


def extract_job_from_message(msg: dict) -> (str, int, str, int, list):
    chat_id = msg['chat']['id']
    reply_to = msg['message_id']
    username = msg['chat']['first_name']

    function: str = "no_function"
    collection: list = []

    if 'photo' in msg.keys():
        function = "photo"
        for pic in msg['photo']:
            collection.append(msg['photo'][pic]['file_id'])

    if 'text' in msg.keys():
        content = msg['text']

        first_word: str = content.split(" ")[0].lower()
        if first_word.startswith("/"):
            function = first_word.replace("/", "")

            if function == "start":
                function = "help"

            value = content.replace(first_word, "").strip()
            if value != "" or collection == []:
                collection = value.split(" ")

        else:
            words = len(content.split(" "))
            if first_word in ['cancel'] and words == 1:
                function = 'cancel'
            elif first_word in ['help', 'hi', 'hello'] and words == 1:
                function = 'help'
            else:
                function = "chat"
            value = content
            collection = [value]

    log(msg=f"Function: {function}, Collection: {collection}")

    return function, chat_id, username, reply_to, collection

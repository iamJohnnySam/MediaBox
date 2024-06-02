from shared_models import configuration
from shared_tools.json_editor import JSONEditor

groups: dict[str, list[int]] = {}


def get_group(group: str) -> list[int]:
    global groups
    download_groups()
    if group in groups.keys():
        return groups[group]
    return []


def add_to_group(group: str, chat_id: int) -> bool:
    global groups
    download_groups()
    if group in groups.keys() and chat_id in groups[group]:
        return False

    if group not in groups.keys():
        groups[group] = []

    groups[group].append(chat_id)
    upload_groups()
    return True


def remove_from_group(group: str, chat_id: int) -> bool:
    global groups
    download_groups()
    if group not in groups.keys() or chat_id not in groups[group]:
        return False
    else:
        groups[group].remove(chat_id)
        upload_groups()
        return True


def download_groups():
    global groups
    if groups == {}:
        groups = JSONEditor(configuration.Configuration().telegram["db_groups"]).read()


def upload_groups():
    global groups
    JSONEditor(configuration.Configuration().telegram["db_groups"]).write(data=groups)

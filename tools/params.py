from functools import cache

import global_variables
import refs
from database_manager.json_editor import JSONEditor
from tools.custom_exceptions import UnexpectedOperation

modules: dict[str, dict[str, dict[str, str | bool]]] = JSONEditor(refs.parameter_file).read()
known_hosts: dict[str, dict[str, str]] = JSONEditor(refs.host_file).read()


@cache
def is_module_available(module: str):
    if module in modules.keys():
        return True if global_variables.host in modules[module].keys() else False
    else:
        raise UnexpectedOperation


@cache
def is_parameter_available(module: str, parameter: str):
    return True if parameter in modules[module][global_variables.host].keys() else False


@cache
def get_param(module: str, parameter: str, get_from_connected_host: bool = False):
    if get_from_connected_host:
        if is_parameter_available(module, parameter):
            host = global_variables.host
        else:
            host = get_connected_host()
    else:
        host = global_variables.host

    return modules[module][host][parameter]


@cache
def get_module_hosts(module: str):
    return modules[module].keys()


@cache
def get_connected_host():
    return get_param('socket', 'connect')

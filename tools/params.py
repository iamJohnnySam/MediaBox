from functools import cache

import global_variables
import refs
from tools.custom_exceptions import UnexpectedOperation


@cache
def is_module_available(module: str):
    if module in refs.modules.keys():
        return True if global_variables.host in refs.modules[module].keys() else False
    else:
        raise UnexpectedOperation


@cache
def is_parameter_available(module: str, parameter: str):
    return True if parameter in refs.modules[module][global_variables.host].keys() else False


@cache
def get_param(module: str, parameter: str, get_from_connected_host: bool = False):
    if get_from_connected_host:
        if is_parameter_available(module, parameter):
            host = global_variables.host
        else:
            host = get_connected_host()
    else:
        host = global_variables.host

    return refs.modules[module][host][parameter]


@cache
def get_module_hosts(module: str):
    return refs.modules[module].keys()


@cache
def get_connected_host():
    return get_param('socket', 'connect')

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
def get_param(module: str, parameter: str):
    return refs.modules[module][global_variables.host][parameter]


@cache
def get_module_hosts(module: str):
    return refs.modules[module].keys()

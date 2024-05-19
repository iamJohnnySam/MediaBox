from functools import cache

import global_variables
import refs
from communication_handler import channels
from shared_tools.json_editor import JSONEditor
from shared_tools.custom_exceptions import UnexpectedOperation

modules: dict[str, dict[str, dict[str, str | bool | int | list[str] | dict[str, int]]]] = JSONEditor(
    refs.parameter_file).read()
known_hosts: dict[str, dict[str, str]] = JSONEditor(refs.host_file).read()


@cache
def is_host_known(host: str):
    host = host.lower()
    return host in known_hosts.keys()


def get_static_ip(host: str):
    host = host.lower()
    if host in known_hosts.keys() and "static_ip" in known_hosts[host].keys():
        return known_hosts[host]["static_ip"]
    else:
        return None


def get_host_from_ip(ip: str):
    for host in known_hosts.keys():
        if "static_ip" in known_hosts[host].keys():
            if ip == known_hosts[host]["static_ip"]:
                return host
    return ""


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
            host = get_connected_host().keys()[0]
    else:
        host = global_variables.host

    return modules[module][host][parameter]


@cache
def get_module_hosts(module: str):
    return modules[module].keys()


@cache
def get_connected_host():
    return get_param('socket', 'connect')


def get_connected_host_with_module(module):
    hosts = get_module_hosts(module)
    for host in hosts:
        if host in channels.sockets.keys():
            if channels.sockets[host].is_server_connected:
                return host

        for socket in channels.sockets.keys():
            if channels.sockets[socket].is_server:
                if host in channels.sockets[socket].connections.keys():
                    return host
    return None

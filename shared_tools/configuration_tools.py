from shared_models import configuration
from shared_tools.logger import log


def is_config_enabled(config: dict, module_name: str = "This module") -> bool:
    if config == {} or ("enable" not in config.keys()) or not config["enable"]:
        log(msg=f"{module_name} is not enabled for this host.")
        return False
    return True


def get_host_from_ip(config: dict, ip: str) -> str:
    for host in config:
        if config[host]["static_ip"] == ip.strip():
            return host
    return ""


def get_ip_from_host(config: dict, host: str) -> (str, int):
    expected_connections = config["connect"]
    if host in expected_connections:
        return expected_connections[host]["static_ip"], expected_connections[host]["port"]
    return "", 0


def get_host_with_module(module: str, connect: str = "") -> list[str]:
    hosts = []
    config = configuration.all_config_data
    for host in config.keys():
        if module.lower() in config[host].keys():
            if connect == "":
                if "enable" in config[host][module].keys() and config[host][module]["enable"]:
                    hosts.append(host)
            else:
                if "connect" in config[host][module].keys():
                    if connect in config[host][module]["connect"]:
                        hosts.append(host)
                else:
                    log(msg=f"Reached unexpected configuration "
                            f"when searching for module: {module} and connect: {connect}.")
    return hosts

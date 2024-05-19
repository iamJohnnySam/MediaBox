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

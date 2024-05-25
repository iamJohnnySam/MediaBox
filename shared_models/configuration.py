import platform
from datetime import datetime

from common_workspace import global_var
from shared_tools.custom_exceptions import InvalidConfiguration
from shared_tools.json_editor import JSONEditor
from shared_tools import logger

all_config_data: dict[str, dict[str, str | bool | list | dict]] = {}
config_data_read_time: datetime = datetime.now()
initial_update = False


class Configuration:

    def __init__(self, config_location: str = ""):
        global all_config_data
        global config_data_read_time
        global initial_update

        if config_location == "":
            config_location = "app_config.json"

        self.machine = platform.machine()
        self.host = platform.node().lower()
        self.system = platform.system()

        time_expired = (config_data_read_time - datetime.now()).total_seconds() > 3600
        if time_expired or all_config_data == {}:
            all_config_data = JSONEditor(config_location).read()
            config_data_read_time = datetime.now()

        common_config: dict = all_config_data["COMMON"]

        if self.host in all_config_data.keys():
            host_config: dict = all_config_data[self.host]
        else:
            raise InvalidConfiguration("This host is not in configuration!")

        if type(host_config) is not dict or type(common_config) is not dict:
            raise InvalidConfiguration("Invalid configuration format for host. No dictionary found!")

        self._config = common_config | host_config

        if not initial_update:
            self._update_logger()
            global_var.main_telegram_channel = self.admin["main_telegram_channel"]
            initial_update = True

    def _update_logger(self) -> None:
        logger.logs_location = self.admin["log_location"]
        logger.log_level = self.admin["log_level"]
        logger.log_to_file = self.admin["log_to_file"]
        logger.log_to_console = self.admin["log_to_console"]
        logger.error_codes = self.admin["error_codes"]

    def _get_module_details(self, module: str) -> dict:
        logger.log(msg=f"Reading configuration for module, {module}.")
        if module in self._config.keys():
            data: dict = self._config[module]
        else:
            logger.log(msg=f"Could not find the module, {module} in configuration file.")
            return {}

        if type(data) is dict:
            return data
        else:
            logger.log(msg=f"Configuration for {module} is not a dictionary.")
            return {}

    def is_module_available(self, module: str):
        return False if self._get_module_details(module) == {} else True

    @property
    def commands(self):
        return self._get_module_details("commands")

    @property
    def admin(self):
        return self._get_module_details("admin")

    @property
    def telegram(self):
        return self._get_module_details("telegram")

    @property
    def socket(self):
        return self._get_module_details("socket")

    @property
    def media(self):
        return self._get_module_details("media")

    @property
    def cctv(self):
        return self._get_module_details("cctv")

    @property
    def news(self):
        return self._get_module_details("news")

    @property
    def finance(self):
        return self._get_module_details("finance")

    @property
    def baby(self):
        return self._get_module_details("baby")

    @property
    def web(self):
        return self._get_module_details("web")

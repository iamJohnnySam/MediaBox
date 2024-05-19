import platform
from datetime import datetime

from shared_tools.custom_exceptions import InvalidConfiguration
from shared_tools.json_editor import JSONEditor
from shared_tools import logger

config_data = {}
config_data_read_time: datetime = datetime.now()
updated_logger = False


class Configuration:

    def __init__(self, config_location: str = "app_config.json"):
        global config_data
        global config_data_read_time

        self.machine = platform.machine()
        self.host = platform.node().lower()
        self.system = platform.system()

        time_expired = (config_data_read_time - datetime.now()).total_seconds() > 3600
        if time_expired or config_data == {}:
            config_data = JSONEditor(config_location).read()
            config_data_read_time = datetime.now()

        if self.host in config_data.keys():
            self._config: dict = config_data[self.host]
        else:
            raise InvalidConfiguration("This host is not in configuration!")

        if type(self._config) is not dict:
            raise InvalidConfiguration("Invalid configuration format for host. No dictionary found!")

        if not updated_logger:
            self._update_logger()

    def _update_logger(self) -> None:
        logger.logs_location = self._config["admin"]["log_location"]
        logger.log_level = self._config["admin"]["log_level"]
        logger.log_to_file = self._config["admin"]["log_to_file"]
        logger.log_to_console = self._config["admin"]["log_to_console"]
        logger.error_codes = self._config["admin"]["error_codes"]

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
    def telegram(self):
        return self._get_module_details("telegram")

    @property
    def socket(self):
        return self._get_module_details("socket")

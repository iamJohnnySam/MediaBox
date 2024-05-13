import platform

import global_variables
from shared_tools.json_editor import JSONEditor
from shared_tools.logger import log


class Configuration:

    def __init__(self, file_location="app_config.json"):
        self.machine = platform.machine()
        self.host = platform.node().lower()
        self.system = platform.system()

        file_data: dict = JSONEditor(file_location).read()
        if self.host in file_data.keys():
            self._config: dict = file_data[self.host]
        else:
            global_variables.flag_stop = True
            return

        if type(self._config) is not dict:
            global_variables.flag_stop = True
            return

    def get_value(self, module: str) -> dict | bool:
        log(msg=f"Reading configuration for module, {module}.")
        if module in self._config.keys():
            data: dict = self._config[module]
        else:
            log(msg=f"Could not find the module, {module} in configuration file.")
            return False

        if type(data) is dict and "enable" in data.keys():
            if data["enable"]:
                return data
            else:
                return False
        else:
            log(msg=f"Could not determine 'enable' state for module, {module}.")
            return False

    @property
    def telegram(self):
        return self.get_value("telegram")

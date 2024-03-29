import json
import os

import logger


class JSONEditor:

    def __init__(self, location):
        self.file = location

        if not os.path.exists(location):
            os.makedirs(os.path.dirname(location), exist_ok=True)
            with open(location, "w") as f:
                json.dump({}, f)

    def add_level1(self, data):
        logger.log("Added Level 1 data: " + str(list(data.keys())[0]) + " at " + self.file)
        with open(self.file, 'r+') as file:
            file_data = json.load(file)
            file_data.update(data)
            file.seek(0)
            json.dump(file_data, file, indent=4)

    def add_level2(self, level, data):
        logger.log("Added Level 2 data: " + str(list(data.keys())[0]) + " to " + level + " at " + self.file)
        with open(self.file, 'r+') as file:
            file_data = json.load(file)
            file_data[level].append(data)
            file.seek(0)
            json.dump(file_data, file, indent=4)

    def read(self):
        with open(self.file, 'r') as file:
            logger.log("Loaded - " + str(self.file))
            return json.load(file)

    def delete(self, keep_keys):
        logger.log("-------DATABASE CLEANUP STARTED-------")

        with open(self.file, 'r+') as file:
            data = json.load(file)

        for key in data.copy().keys():
            if key not in keep_keys:
                del data[key]
                logger.log("Deleted Key - " + str(key))

        with open(self.file, 'w+') as file:
            json.dump(data, file, indent=4)

        logger.log("-------DATABASE CLEANUP ENDED-------")

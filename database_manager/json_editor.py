import json
import logger


class JSONEditor:

    def __init__(self, location):
        self.file = location

    def add_level1(self, data):
        logger.log('info', "Added Level 1 data: " + str(data) + " at " + self.file)
        with open(self.file, 'r+') as file:
            file_data = json.load(file)
            file_data.update(data)
            file.seek(0)
            json.dump(file_data, file, indent=4)

    def add_level2(self, level, data):
        logger.log('info', "Added Level 2 data: " + str(data) + " to " + level + " at " + self.file)
        with open(self.file, 'r+') as file:
            file_data = json.load(file)
            file_data[level].append(data)
            file.seek(0)
            json.dump(file_data, file, indent=4)

    def read(self):
        with open(self.file, 'r') as file:
            return json.load(file)

    def delete(self, keep_keys):
        with open(self.file, 'r+') as file:
            data = json.load(file)

        for key in data.copy().keys():
            if key not in keep_keys:
                del data[key]

        with open(self.file, 'w+') as file:
            json.dump(data, file, indent=4)
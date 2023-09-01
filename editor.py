import json


class JSONEditor:

    def __init__(self, location):
        self.file = location

    def add_level1(self, data):
        with open(self.file, 'r+') as file:
            file_data = json.load(file)
            file_data.update(data)
            file.seek(0)
            json.dump(file_data, file, indent=4)

    def add_level2(self, level, data):
        with open(self.file, 'r+') as file:
            file_data = json.load(file)
            file_data[level].append(data)
            file.seek(0)
            json.dump(file_data, file, indent=4)

    def read(self):
        with open(self.file, 'r') as file:
            return json.load(file)
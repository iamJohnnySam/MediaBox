import os


class RefactorFolder:
    def __init__(self, path):
        self.path = path

    def clean_all(self):
        for root, dirs, files in os.walk(self.path):
            for file in files:
                self.clean_up_file(file)

    def clean_up_file(self, file):
        pass

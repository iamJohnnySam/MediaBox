import json
import os
import threading
from functools import wraps
from json import JSONDecodeError

from shared_tools.logger import log

threading_locks = {}


def thread_safe(func):
    @wraps(func)
    def wrapper(self, job_id=0, *arg, **kw):
        if self.file in threading_locks.keys():
            self.lock = threading_locks[self.file]
        else:
            self.lock = threading.Lock()
            threading_locks[self.file] = self.lock

        self.lock.acquire()
        log(job_id=job_id, msg=f"Thread lock acquired")
        res = func(self, *arg, **kw)
        self.lock.release()
        log(job_id=job_id, msg=f"Thread lock released")
        return res

    return wrapper


class JSONEditor:

    def __init__(self, location):
        self.file = location

    @thread_safe
    def write(self, data: dict, job_id=0):
        if not os.path.exists(self.file):
            os.makedirs(os.path.dirname(self.file), exist_ok=True)

        with open(self.file, "w") as f:
            json.dump(data, f, indent=4)

        log(job_id=job_id, msg=f"Updated file: {self.file}")

    @thread_safe
    def add_level1(self, data, job_id=0):
        if not os.path.exists(self.file):
            os.makedirs(os.path.dirname(self.file), exist_ok=True)

            with open(self.file, "w") as f:
                f.seek(0)
                json.dump({}, f)

        log(job_id=job_id, msg="Added Level 1 data: " + str(list(data.keys())[0]) + " at " + self.file)

        file_data = self.read_json()
        if file_data == "":
            file_data = {}
        file_data.update(data)

        with open(self.file, 'r+') as file:
            file.seek(0)
            json.dump(file_data, file, indent=4)

    @thread_safe
    def add_level2(self, level, data, job_id=0):
        file_data = self.read_json()
        file_data[level].append(data)

        log(job_id=job_id, msg="Added Level 2 data: " + str(list(data.keys())[0]) + " to " + level + " at " + self.file)
        with open(self.file, 'r+') as file:
            file.seek(0)
            json.dump(file_data, file, indent=4)

    @thread_safe
    def read(self, job_id=0):
        return self.read_json()

    @thread_safe
    def inv_delete(self, keep_keys, job_id=0):
        data = self.read_json()

        for key in data.copy().keys():
            if key not in keep_keys:
                del data[key]
                log(job_id=job_id, msg="Deleted Key - " + str(key))

        with open(self.file, 'w+') as file:
            json.dump(data, file, indent=4)

    @thread_safe
    def delete(self, key: str, job_id=0, sub_key: str = None):
        data: dict = self.read_json()

        if key in data.copy().keys():
            del data[key]
            log(job_id=job_id, msg="Deleted Key - " + str(key))

        if sub_key is not None:
            for key in data.copy().keys():
                if sub_key in key:
                    del data[key]
                    log(job_id=job_id, msg="Deleted Key due to sub key - " + str(key))

        with open(self.file, 'w+') as file:
            json.dump(data, file, indent=4)

        log(job_id=job_id, msg="Deleted Key - " + str(key))

    def read_json(self):
        try:
            with open(self.file, 'r+') as file:
                data: dict = json.load(file)
        except JSONDecodeError as e:
            with open(self.file, 'r') as file:
                content = file.read()
            if content.endswith('}}'):
                modified_content = content[:-1]
                with open(self.file, 'w') as file:
                    file.write(modified_content)
            with open(self.file, 'r+') as file:
                data: dict = json.load(file)
        return data

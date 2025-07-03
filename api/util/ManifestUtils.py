import json

class ManifestEntry :

    def __init__(self, url, file_number, status=False):
        self.url = url
        self.file_number = file_number
        self.status = status

    def set_status(self, status):
        self.status = status

    def json_dump(self):
        return json.dumps(self.__dict__, indent=4)

class Manifest:
    def __init__(self):
        self.entries = []

    def add(self, entry: ManifestEntry):
        self.entries.append(entry)

    def json_dump(self):
        return json.dumps(self.__dict__, indent=4)

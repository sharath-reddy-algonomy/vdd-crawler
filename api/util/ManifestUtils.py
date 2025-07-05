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
        self.success_rate = 0.0

    def calculate_success_rate(self):
        total_entries = len(self.entries)
        total_success = len(list(filter(lambda obj: obj.status is True, self.entries)))
        self.success_rate = (total_success/total_entries)*100


    def add(self, entry: ManifestEntry):
        self.entries.append(entry)
        self.calculate_success_rate()


    def json_dump(self):
        return json.dumps(self.__dict__, indent=4)

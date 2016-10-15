import datetime
import json

from bson import ObjectId

class JSONEncoder(json.JSONEncoder):
    def default(self, object_value):
        if isinstance(object_value, ObjectId):
            return str(object_value)
        elif isinstance(object_value, datetime.datetime):
            return int(object_value.timestamp())
        return json.JSONEncoder.default(self, object_value)

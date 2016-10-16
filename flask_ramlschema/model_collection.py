from bson.objectid import ObjectId

from .errors import DatabaseValidaitionError
from .validate import get_json_errors

class ModelCollection:
    def __init__(self, mongo_collection, model_schema):
        self.model_schema = model_schema
        self.mongo_collection = mongo_collection

    def new(self, document, validate=False, **kwargs):
        if validate:
            self.validate(document)
        return self.mongo_collection.insert_one(document, **kwargs)

    def replace_one_id(self, document_id, document, validate=False, **kwargs):
        if validate:
            self.validate(document)
        mongo_filter = {"_id":document_id}
        return self.mongo_collection.replace_one(
            mongo_filter,
            document,
            **kwargs
            )

    def find_one_id(self, document_id):
        return self.mongo_collection.find_one({"_id":document_id})

    def find_id_list(self, id_list):
        return self.mongo_collection.find({"_id":{"$in":id_list}})

    def find_all(self):
        return self.mongo_collection.find()

    def delete_one_id(self, document_id):
        return self.mongo_collection.delete_one({"_id":document_id})

    def validate(self, document):
        errors = self.get_validation_errors(document)
        if errors:
            raise DatabaseValidaitionError(errors)

    def get_validation_errors(self, document):
        return get_json_errors(document, self.model_schema)

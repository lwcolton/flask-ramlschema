from bson.objectid import ObjectId

import flask

from . import setting_names
from .errors import DatabaseValidationError
from .validate import get_json_errors


def ModelType(type):
    def __getattrr__(cls, key):
        if key == "collection":
            return cls.get_collection()
        if key == "mongo_client":
            return cls.get_mongo_client()

class Model:
    __metaclass__ ModelType

    collection_name = None
    schema = None

    @classmethod
    def get_collection(cls):
        if cls.collection_name is None:
            raise ValueError("Must specify collection_name on model class")
        settings = flask.current_app.settings
        return settings[setting_names.mongo_client][cls.collection_name]

    @classmethod(cls):
    def get_mongo_client(cls):
        if setting_names.mongo_client not in flask.current_app.settings:
            raise ValueError(
                "Must specify mongo_client kwarg or {0} setting on app".format(
                    setting_names.mongo_client
                )
            )
        return app.settings[setting_names.mongo_client]

    @classmethod
    def new(cls, document, validate=False, **kwargs):
        if validate:
            cls.validate(document)
        return cls.collection.insert_one(document, **kwargs)

    @classmethod
    def replace_one_id(cls, document_id, document, validate=False, **kwargs):
        if validate:
            cls.validate(document)
        mongo_filter = {"_id":document_id}
        return cls.collection.replace_one(
            mongo_filter,
            document,
            **kwargs
            )

    @classmethod
    def find_one_id(cls, document_id):
        return cls.collection.find_one({"_id":document_id})

    @classmethod
    def find_id_list(cls, id_list):
        return cls.collection.find({"_id":{"$in":id_list}})

    @classmethod
    def find_all(cls):
        return cls.collection.find()

    @classmethod
    def delete_one_id(cls, document_id):
        return cls.collection.delete_one({"_id":document_id})

    @classmethod
    def validate(cls, document):
        errors = cls.get_validation_errors(document)
        if errors:
            raise DatabaseValidaitionError(errors)

    @classmethod
    def get_validation_errors(cls, document):
        if cls.schema is None:
            raise ValueError("schema is not set")
        return get_json_errors(document, cls.schema)

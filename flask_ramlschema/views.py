import json
import logging

from bson.objectid import ObjectId
import bson.json_util
from flask import abort, request, Response
from flask.views import MethodView
from jsonschema import Draft4Validator
import pymongo
import yaml

from .errors import ValidationError
from .json_encoder import JSONEncoder
from .pagination import get_pagination_args, get_pagination_wrapper

class APIMixin:
    def __init__(self, url_path, logger=None, mongo_collection=None, 
                 mongo_collection_func=None):
        if url_path.endswith("/"):
            url_path = url_path[:-1]
        self.url_path = url_path
        self.name = self.get_name(url_path)
        if logger is None:
            logger = logging.getLogger(__name__)
        self.logger = logger
        self._mongo_collection = mongo_collection
        if mongo_collection_func is not None:
            self._get_mongo_collection = mongo_collection_func
        else:
            self._get_mongo_collection = self._default_get_mongo_collection

    def get_name(self, path):
        path_parts = path.split("/")
        if not path_parts[0]:
            path_parts = path_parts[1:]
        return path_parts[0]

    @property
    def mongo_collection(self):
        return self._get_mongo_collection()

    def _default_get_mongo_collection(self):
        return self._mongo_collection

    def get_request_json(self, schema):
        request_body = json.loads(request.data.decode("utf-8"))
        errors = self.get_request_errors(request_body, schema)
        if errors:
            raise ValidationError(errors)
        return request_body

    def set_response_json(self, response, response_dict, status=200):
        response.data = JSONEncoder().encode(response_dict)
        response.mimetype = "application/json"
        response.status_code = 200

    def get_request_errors(self, request_body, schema):
        validator = Draft4Validator(schema)
        request_errors = []
        for error in validator.iter_errors(request_body):
            error_dict = {
                "message":error.message
            }
            request_errors.append(error_dict)
        return request_errors

    def find_one_or_404(self, query):
        document = self.mongo_collection.find_one(query)
        if not document:
            abort(404)
        return document

class JSONSchemaView(MethodView, APIMixin):
    def __init__(self, schema, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.schema = schema

    @property
    def reqeust_body(self):
        request_body = self.get_request_json(self.schema)
        return request_body


class RAMLResource(APIMixin):
    def __init__(self, collection_raml, item_raml, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url_path_collection = self.url_path
        self.url_path_item_id = "{0}/<document_id>".format(self.url_path)
        self.parse_raml(collection_raml, item_raml)

    @classmethod
    def from_files(cls, flask_app, collection_raml_path, item_raml_path, *args, **kwargs):
        collection_raml = cls.load_raml_file(collection_raml_path)
        item_raml = cls.load_raml_file(item_raml_path)
        resource = cls(collection_raml, item_raml, *args, **kwargs)
        resource.init_app(flask_app)
        return resource

    def parse_raml(self, collection_raml, item_raml):
        self.parse_raml_collection(collection_raml)
        self.parse_raml_item(item_raml)

    @classmethod
    def load_raml_file(cls, raml_file_path):
        with open(raml_file_path, "r") as raml_handle:
            raml = yaml.load(raml_handle.read())
            return raml

    def parse_raml_collection(self, collection_raml):
        if "collection" in collection_raml["type"]:
            self.collection_type = "collection"
            self.new_item_schema = json.loads(collection_raml["type"][self.collection_type]["newItemSchema"])
        elif "read-only-collection" in collection_raml["type"]:
            self.collection_type = "read-only-collection"
        else:
            raise ValueError("Must be of type 'collection' or 'read-only-collection")
        

    def parse_raml_item(self, item_raml):
        if "collection-item" in item_raml["type"]:
            self.item_type = "collection-item"
            self.update_item_schema = json.loads(item_raml["type"][self.item_type]["updateItemSchema"])
        elif "read-only-collection-item" in item_raml["type"]:
            self.item_type = "read-only-collection-item"
        else:
            raise ValueError("Must be of type 'collection-item' or 'read-only-collection-item'")

    def init_app(self, flask_app, collection_name=None, collection_items_name=None):
        if collection_name is None:
            collection_name = self.name + "_collection"
        if collection_items_name is None:
            collection_items_name = self.name + "_item"
        self.logger.info("Adding url rule for {0} at {1}".format(collection_name, self.url_path_collection))
        flask_app.add_url_rule(
            self.url_path_collection,
            collection_name, 
            self._collection_endpoint, 
            methods=["GET", "POST"])
        self.logger.info("Adding url rule for {0} at {1}".format(collection_items_name, self.url_path_item_id))
        flask_app.add_url_rule(
            self.url_path_item_id, 
            collection_items_name, 
            self._collection_items_endpoint, 
            methods=["GET", "POST", "DELETE"])

    def _collection_endpoint(self):
        if request.method == "POST":
            if self.collection_type != "read-only-collection":
                return self._create_view()
        elif request.method == "GET":
            return self._list_view()
        abort(405)

    def _collection_items_endpoint(self, document_id):
        if request.method == "POST":
            if self.collection_type != "read-only-collection":
                return self._update_view(document_id)
        elif request.method == "GET":
            return self._item_view(document_id)
        elif request.method == "DELETE":
            if self.collection_type != "read-only-collection":
                return self._delete_view(document_id)
        abort(405)

    def create_view(self, document):
        return self.mongo_collection.insert_one(document)

    def _create_view(self):
        request_dict = self.get_request_json(self.new_item_schema)
        document = request_dict["item"]
        if not self.create_allowed(document):
            abort(401)
            return
        result = self.create_view(document)
        document["id"] = str(document["_id"])
        del document["_id"]
        response = Response()
        self.set_response_json(response, {"item":document})
        return response

    def create_allowed(self, document):
        return True

    def list_view(self):
        find_cursor = self.mongo_collection.find()
        return find_cursor

    def _list_view(self):
        if not self.list_allowed():
            abort(401)
            return
        page, per_page, sort_by, order, order_arg = get_pagination_args(request)
        find_cursor = self.list_view()
        page_wrapper = get_pagination_wrapper(find_cursor, page, per_page, sort_by, order, order_arg)
        response = Response()
        self.set_response_json(response, page_wrapper)
        return response

    def list_allowed(self):
        return True


    def item_view(self, document_id):
        object_id = ObjectId(document_id)
        return self.find_one_or_404({"_id":object_id})

    def _item_view(self, document_id):
        if not self.item_view_allowed(document_id):
            abort(401)
            return
        document = self.item_view(document_id)
        response = Response()
        if document is None:
            response.status_code = 404
            return response
        document["id"] = document_id
        del document["_id"]
        self.set_response_json(response, {"item":document})
        return response

    def item_view_allowed(self, document_id):
        return True

    def update_view(self, update_document, existing_document):
        new_document = existing_document.copy()
        new_document.update(update_document)
        return new_document

    def _update_view(self, document_id):
        object_id = ObjectId(document_id)
        existing_document = self.find_one_or_404({"_id":object_id})
        request_dict = self.get_request_json(self.update_item_schema)
        update_document = request_dict["item"]
        if not self.update_allowed(update_document, existing_document):
            abort(401)
            return
        document = self.update_view(update_document, existing_document)
        self.mongo_collection.find_one_and_replace({"_id":object_id}, document)
        response = Response()
        response.status_code = 204
        return response

    def update_allowed(self, update_document, existing_document):
        return True

    def delete_view(self, document_id):
        if not self.delete_allowed(document_id):
            abort(401)
            return
        object_id = ObjectId(document_id)
        document = self.mongo_collection.find_one_and_delete({"_id":object_id})
        if not document:
            abort(404)

    def _delete_view(self, document_id):
        self.delete_view(document_id)
        response = Response()
        response.status_code = 204
        return response

    def delete_allowed(self, document_id):
        return True


import json
import logging

from bson.objectid import ObjectId
import bson.json_util
from flask import abort, request, Response
from flask.views import MethodView
from jsonschema import Draft4Validator
import pymongo
import yaml

from .errors import ValidationError, register_error_handlers
from .json_encoder import JSONEncoder
from .pagination import get_page

class APIView(MethodView):
    """Provides basic API utilities like validation and json decoding


    You can subclass `APIView` to make a basic API endpoint,
    it inherits from `flask.MethodView <http://flask.pocoo.org/docs/0.11/views/#method-based-dispatching>`_.

    Example:
    .. code-block:: python

        from flask import Flask
        from flask_ramlschema.views import APIView
        from flask_ramlschema.errors import register_error_handlers

        class MyAPIEndpoint(APIView):
            post_schema = {
              "$schema": "http://json-schema.org/draft-04/schema#",
              "type": "object",
              "properties": {
                "myfield": {
                  "type": "string"
                }
              },
              "required": [
                "myfield"
              ]
            }

            def post(self):
                # Use jsonschema to validate input
                jsonschema = self.post_schema
                body = self.get_request_json(self.post_schema)

                #Do something with body data
                print(body["myfield"])

                #Return API response in JSON
                return self.json_response({"success":True})

        app = Flask("my_api")
        register_error_handlers(app)
        app.add_url_rule("/my-endpoint", view_func=MyAPIEndpoint.as_view())


    You can generate jsonschema from example documents using `jsonschema.net <http://jsonschema.net/#/>`.

    """

    def get_request_json(self, schema):
        """Reads the request body and decodes it as JSON, validating it against ``schema``.

        :param schema dict: JSONSchema v4 that has been loaded into a python dictionary.
            This is used to validate the incoming data.  If validation fails, 
            ``errors.ValidationError`` is raised.  You can use ``errors.register_error_handlers``
            to register an error handler that will convert ``ValidationError`` instances into
            JSON responses.
        """
        request_body = json.loads(request.data.decode("utf-8"))
        errors = self.get_request_errors(request_body, schema)
        if errors:
            raise ValidationError(errors)
        return request_body

    def get_request_errors(self, request_body, schema):
        validator = Draft4Validator(schema)
        request_errors = []
        for error in validator.iter_errors(request_body):
            error_dict = {
                "message":error.message
            }
            request_errors.append(error_dict)
        return request_errors

    def json_response(self, response_dict, response_obj=None, status=200):
        """Encodes ``response_dict`` as json, returning a response with the body set.

        :param response_dict dict: Dictionary to encode as JSON for response body.
        :param response_obj flask.Response: (Optional) The response object to use.
        :param status int: (Optional) Status code of the response.
        """
        if response_obj is None:
            response_obj = Response()
        response_obj.data = JSONEncoder().encode(response_dict)
        response_obj.mimetype = "application/json"
        response_obj.status_code = 200
        return response_obj

class MongoView(APIView):
    """Subclass of APIView that stores a connection to mongodb."""
    def __init__(self, *args, mongo_collection=None,
                 mongo_collection_func=None, mongo_collection_name=None,
                 logger=None, **kwargs):
        super().__init__(*args, **kwargs)
        if logger is None:
            logger = logging.getLogger(__name__)
        self.logger = logger
        self.mongo_collection_name = mongo_collection_name
        self._mongo_collection = mongo_collection
        if mongo_collection_func is not None:
            self._get_mongo_collection = mongo_collection_func
        else:
            if mongo_collection is None:
                raise ValueError(
                    "Must specify either mongo_collection or mongo_collection_func"
                    )
            self._get_mongo_collection = self._default_get_mongo_collection

    @property
    def mongo_collection(self):
        return self._get_mongo_collection(self.mongo_collection_name)

    def _default_get_mongo_collection(self, mongo_collection_name):
        return self._mongo_collection

    def find_one_or_404(self, query):
        document = self.mongo_collection.find_one(query)
        if not document:
            abort(404)
        return document


class RAMLResource(MongoView):
    def __init__(self, collection_raml, item_raml, *args, 
                 url_path=None, flask_app=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.parse_raml(collection_raml, item_raml)
        if url_path:
            if not flask_app:
                raise ValueError("If setting url_path must also provide flask_app")
            self.add_routes(url_path, flask_app)

    @classmethod
    def from_files(cls, collection_raml_path, item_raml_path, *args, **kwargs):
        collection_raml = cls.load_raml_file(collection_raml_path)
        item_raml = cls.load_raml_file(item_raml_path)
        # Not using as_view here because it instaniates the class on every request
        resource = cls(collection_raml, item_raml, *args, **kwargs)
        return resource

    def add_routes(self, url_path, flask_app):
        while url_path.endswith("/"):
            url_path = url_path[:-1]
        url_parts = url_path.split("/")
        resource_name = url_parts[-1]
        collection_endpoint_name = resource_name + "_collection"
        item_endpoint_name = resource_name + "_item"
        url_path_collection = url_path
        url_path_item = "{0}/<string:item_id>".format(url_path)
        self.logger.info("Adding url rule for endpoint {0} at {1}".format(
            collection_endpoint_name, url_path_collection)
            )
        flask_app.add_url_rule(
            url_path_collection, 
            endpoint=collection_endpoint_name,
            view_func=self.dispatch_request,
            methods=["GET", "POST"],
            defaults={"item_id":None}
            )
        self.logger.info("Adding url rule for {0} at {1}".format(
            item_endpoint_name, url_path_item)
            )
        flask_app.add_url_rule(
            url_path_item, 
            endpoint=item_endpoint_name, 
            view_func=self.dispatch_request,
            methods=["GET", "POST", "DELETE"]
            )

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

    def get(self, item_id):
        if item_id is None:
            return self._list_view()
        else:
            return self._item_view(item_id)

    def post(self, item_id):
        if self.collection_type == "read-only-collection":
            abort(405)
        else:
            if item_id is None:
                return self._create_view()
            else:
                return self._update_view(item_id)

    def delete(self, item_id):
        if self.collection_type == "read-only-collection":
            abort(405)
        elif item_id is None:
            abort(404)
        return self._delete_view(item_id)

    def create_view(self, document):
        """Inserts a document into a collection
        Called on POST to /<collection>
        The default implementation calls ``pymongo.Collection.insert_one``
        To implement custom create behavior, override this method.

        :param document dict: Validated JSON from reqest body.

        ..code-block:: python

            class MyAPIResource(RAMLResource):
                def create_view(self, document):
                    action_result = custom_action(document)
                    insert_result = self.mongo_collection.insert_one(document)
        """
        result = self.mongo_collection.insert_one(document)
        document["id"] = str(result.inserted_id)

    def _create_view(self):
        request_dict = self.get_request_json(self.new_item_schema)
        document = request_dict
        if not self.create_allowed(document):
            abort(401)
            return
        self.create_view(document)
        response = self.json_response(document)
        return response

    def create_allowed(self, document):
        return True

    def list_view(self):
        """Lists documents from a collection.

        You can override this to implement custom list behavior

        ..code-block:: python

            class MyAPIResource(RAMLResource):
                def list_view(self):
                    return [{"id":1, myfield":"foo"}, {"id":2, myfield":"bar"}]
        """
        find_cursor = self.mongo_collection.find()
        return find_cursor

    def _list_view(self):
        if not self.list_allowed():
            abort(401)
            return
        find_cursor = self.list_view()
        page = get_page(find_cursor)
        response = self.json_response(page)
        return response

    def list_allowed(self):
        return True


    def item_view(self, document_id):
        """Responds with details about a specific item.

        Override this to implement a custom item view.

        :param document_id string:  ID of the document to display, from url parameter
        """
        object_id = ObjectId(document_id)
        return self.find_one_or_404({"_id":object_id})

    def _item_view(self, document_id):
        if not self.item_view_allowed(document_id):
            abort(401)
            return
        document = self.item_view(document_id)
        if document is None:
            return Response(status=404)
        document["id"] = document_id
        del document["_id"]
        response = self.json_response(document)
        return response

    def item_view_allowed(self, document_id):
        return True

    def update_view(self, update_document, existing_document):
        """Updates a document in the database.

        Override this to implement custom update behavior.

        :param update_document dict: Validated request body
        :param existing_document dict: Document as it exists in mongodb now
        """
        new_document = existing_document.copy()
        new_document.update(update_document)
        return new_document

    def _update_view(self, document_id):
        object_id = ObjectId(document_id)
        existing_document = self.find_one_or_404({"_id":object_id})
        request_dict = self.get_request_json(self.update_item_schema)
        update_document = request_dict
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
        """Deletes a document from the database.

        Override this to implement custom delete behavior.

        :param document_id str: ID of the document to delete, from url parameter
        """
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


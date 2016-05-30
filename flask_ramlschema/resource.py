from bson.objectid import ObjectId
import bson.json_util
from flask import abort, request, Response
import json
import jsonschema
import math
import pymongo
import yaml

from .json_encoder import JSONEncoder

class RAMLResource:
    def __init__(self, collection_raml, item_raml, url_path,
                 logger, mongo_client, database_name, mongo_collection_name=None):
        if url_path.endswith("/"):
            url_path = url_path[:-1]
        self.url_path = url_path
        self.url_path_collection = self.url_path
        self.url_path_item_id = "{0}/<document_id>".format(url_path)
        self.name = self.get_name(url_path)
        self.logger = logger
        self.mongo_client = mongo_client
        self.database_name = database_name
        if mongo_collection_name is None:
            mongo_collection_name = self.name
        self.mongo_collection_name = mongo_collection_name
        self.mongo_collection = self.mongo_client[self.database_name][self.mongo_collection_name]
        self.parse_raml(collection_raml, item_raml)

    @classmethod
    def from_files(cls, flask_app, collection_raml_path, item_raml_path, *args, **kwargs):
        collection_raml = cls.load_raml_file(collection_raml_path)
        item_raml = cls.load_raml_file(item_raml_path)
        resource = cls(collection_raml, item_raml, *args, **kwargs)
        resource.init_app(flask_app)
        return resource

    def get_name(self, path):
        path_parts = path.split("/")
        if not path_parts[0]:
            path_parts = path_parts[1:]
        return path_parts[0]

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

    def get_request_json(self):
        request_dict = json.loads(request.data.decode("utf-8"))
        return request_dict

    def set_response_json(self, response, response_dict, status=200):
        response.data = JSONEncoder().encode(response_dict)
        response.mimetype = "application/json"
        response.status_code = 200

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
        request_dict = self.get_request_json()
        document = request_dict["item"]
        jsonschema.validate(document, self.new_item_schema)
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
        page, per_page, sort_by, order, order_arg = self.get_pagination_args()
        find_cursor = self.list_view()
        page_wrapper = self.get_pagination_wrapper(find_cursor, page, per_page, sort_by, order, order_arg)
        response = Response()
        self.set_response_json(response, page_wrapper)
        return response

    def list_allowed(self):
        return True

    def get_pagination_args(self, max_per_page=100):
        page = request.args.get("page", 1)
        per_page = request.args.get("per_page", 25)
        if per_page > max_per_page:
            raise ValueError("per_page cannot be greated than 100")

        sort_by = request.args.get("sort_by", "id")
        if sort_by == "id":
            sort_by = "_id"

        # order values based on backbone-paginator
        order_arg = request.args.get("order", 1)
        if order_arg == 1:
            order = pymongo.DESCENDING
        else:
            order = pymongo.ASCENDING

        return page, per_page, sort_by, order, order_arg

    def get_pagination_wrapper(self, find_cursor, page, per_page, sort_by, order, order_arg):
        total_entries = find_cursor.count()
        page_wrapper = {}
        page_wrapper["page"] = page
        page_wrapper["per_page"] = per_page
        page_wrapper["total_pages"] = int(math.ceil(total_entries / float(page_wrapper["per_page"])))
        page_wrapper["total_entries"] = total_entries
        page_wrapper["sort_by"] = sort_by
        page_wrapper["order"] = order_arg

        if page_wrapper["page"] > page_wrapper["total_pages"] or page_wrapper["page"] < 1:
            if total_entries != 0 or page_wrapper["page"] != 1:
                raise ValueError("invalid page number: {0]".format(page_wrapper["page"]))
        skip_num = per_page*(page-1)
        find_cursor.sort(sort_by, order).skip(skip_num).limit(per_page)
        items = list(find_cursor)
        for mongo_doc in items:
            mongo_doc["id"] = mongo_doc["_id"]
            del mongo_doc["_id"]
        page_wrapper["items"] = items
        return page_wrapper

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
        request_dict = self.get_request_json()
        update_document = request_dict["item"]
        jsonschema.validate(update_document, self.update_item_schema)
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

    def find_one_or_404(self, query):
        document = self.mongo_collection.find_one(query)
        if not document:
            abort(404)
        return document
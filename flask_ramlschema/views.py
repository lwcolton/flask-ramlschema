import json
import logging

from bson.objectid import ObjectId
import bson.json_util
from flask import abort, request, Response
from flask.views import MethodView

import pymongo
import yaml

from .errors import BodyValidationHTTPError, BodyDecodeHTTPError, InvalidPageHTTPError
from .errors import InvalidPageError
from .json_encoder import JSONEncoder
from .pagination import get_page
from .validate import get_json_errors

class APIView(MethodView):

    body_validation_error_class = BodyValidationHTTPError
    body_decode_error_class = BodyDecodeHTTPError

    def get_request_json(self, schema):
        request_body = self.decode_request_json()
        errors = get_json_errors(request_body, schema)
        if errors:
            raise self.body_validation_error_class(errors)
        return request_body

    def set_response_json(self, response, response_dict, status=200):
        response.data = JSONEncoder().encode(response_dict)
        response.mimetype = "application/json"
        response.status_code = 200

    def decode_request_json(self):
        try:
            request_body = json.loads(request.data.decode("utf-8"))
        except json.JSONDecodeError as decode_error:
            raise self.body_decode_error_class(decode_error)


class ModelView(APIView):

    invalid_page_error_class = InvalidPageHTTPError

    def __init__(self, model_collection, logger=None):
        if logger is None:
            logger = logging.getLogger(__name__)
        self.logger = logger
        self.add_routes(url_path, flask_app)

    def find_one_or_404(self, document_id):
        document = self.model_collection.find_one_id(document_id)
        if not document:
            abort(404)
        return document

    def decode_document_id(self, document, id_param):
        if self.use_object_id:
            document_id = ObjectId(document_id)
            document["_id"] = document_id
        return document_id

    def create_view(self):
        request_dict = self.get_request_json(self.new_item_schema)
        document = request_dict
        if not self.create_allowed(document):
            abort(401)
        result = self.model_collection.new(document)
        response = Response()
        self.set_response_json(response, document)
        return response

    def create_allowed(self, document):
        return True

    def list_view(self):
        if not self.list_allowed():
            abort(401)
            return
        find_cursor = self.model_collection.find_all()
        try:
            page = get_page(find_cursor)
        except InvalidPageError as invalid_page_error:
            raise InvalidPageHTTPError(invalid_page_error.page_num)
        response = Response()
        self.set_response_json(response, page)
        return response

    def list_allowed(self):
        return True

    def item_view(self, document_id):
        document_id = self.decode_document_id(document, document_id)
        if not self.item_view_allowed(document_id):
            abort(401)
        document = self.find_one_or_404({"_id":document_id})
        response = Response()
        self.set_response_json(response, document)
        return response

    def item_view_allowed(self, document_id):
        return True

    def replace_view(self, document_id):
        document = self.get_request_json(self.item_schema)
        if not self.use_string_id:
            document_id = ObjectId(document_id)
            document["_id"] = document_id
        if not self.replace_allowed(document_id):
            abort(401)
            return
        result = self.model_collection.replace_one_id({"_id":document_id}, document)
        if result.matched_count != 1:
            abort(404)
        response = Response()
        response.status_code = 204
        return response

    def replace_allowed(self, document_id):
        return True

    def delete_view(self, document_id):
        if not self.delete_allowed(document_id):
            abort(401)
        object_id = ObjectId(document_id)
        document = self.model_collection.delete_one_id({"_id":object_id})
        if not document:
            abort(404)
        response = Response()
        response.status_code = 204
        return response

    def delete_allowed(self, document_id):
        return True

import json
import logging

from bson.objectid import ObjectId
import bson.json_util
from flask import abort, request, Response
from flask.views import MethodView

import pymongo
import yaml

from ..errors import BodyValidationHTTPError, BodyDecodeHTTPError
from ..errors import InvalidPageHTTPError, InvalidPageError
from ..json_encoder import JSONEncoder
from ..pagination import get_page
from ..validate import get_json_errors
from . import ModelView

class CollectionView(ModelView):
    invalid_page_error_class = InvalidPageHTTPError

    def get(self):
        if not self.get_allowed():
            abort(401)
            return
        find_cursor = self.model.find_all()
        try:
            page = get_page(find_cursor)
        except InvalidPageError as invalid_page_error:
            raise self.invalid_page_error_class(invalid_page_error.page_num)
        response = Response()
        self.set_response_json(response, page)
        return response

    def get_allowed(self):
        return True

    def post(self):
        document = flask.request.json
        if not self.post_allowed(document):
            abort(401)
        result = self.model.new(document)
        response = Response()
        self.set_response_json(response, document)
        return response

    def post_allowed(self, document):
        return True

class CollectionItemView(ModelView):
    def decode_document_id(self, document, id_param):
        if self.use_object_id:
            document_id = ObjectId(document_id)
            document["_id"] = document_id
        return document_id

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

    def update_view(self, document_id):
        update_document = flask.request.json
        if not self.use_string_id:
            document_id = ObjectId(document_id)
            update_document["_id"] = document_id
        if not self.update_allowed(document_id):
            abort(401)
        existing_document = self.find_one_or_404(document_id)
        for update_key, update_value in update_document.items():
            existing_document[update_key] = update_value
        result = self.model.replace_one_id(
            {"_id":document_id}, existing_document
            )
        if result.matched_count != 1:
            abort(404)
        response = Response()
        response.status_code = 204
        return response

    def update_allowed(self, document_id):
        return True

    def delete_view(self, document_id):
        if not self.delete_allowed(document_id):
            abort(401)
        object_id = ObjectId(document_id)
        document = self.model.delete_one_id({"_id":object_id})
        if not document:
            abort(404)
        response = Response()
        response.status_code = 204
        return response

    def delete_allowed(self, document_id):
        return True

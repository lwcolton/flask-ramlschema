import copy
import json
import logging
import os.path
import sys
from unittest import TestCase, mock
import uuid

from bson.objectid import ObjectId
from flask import Flask
from flask_ramlschema.views import RAMLResource

logger = logging.getLogger(__name__)

class TestExampleApp(TestCase):
    def setUp(self):
        tests_dir = os.path.dirname(sys.modules[__name__].__file__)
        collection_raml_file = os.path.abspath(os.path.join(tests_dir, "../raml/resources/cats-collection.raml"))
        item_raml_file = os.path.abspath(os.path.join(tests_dir, "../raml/resources/cats-item.raml"))
        self.mongo_client = mock.MagicMock()
        self.mongo_collection = mock.MagicMock()
        self.flask_app = Flask("test_app")
        self.flask_app.config['TESTING'] = True
        self.resource = RAMLResource.from_files(
            collection_raml_file, item_raml_file, 
            url_path="/cats", flask_app=self.flask_app,
            mongo_collection = self.mongo_collection
            )
        self.test_client = self.flask_app.test_client()

    def tearDown(self):
        mock.patch.stopall()

    def test_list(self):
        test_document_id = ObjectId()
        test_document = {"_id":test_document_id, "breed":"tabby", "name":"muffins"}
        test_result_document = copy.deepcopy(test_document)
        test_result_document["id"] = str(test_result_document["_id"])
        del test_result_document["_id"]
        test_list = [test_document]
        test_result_list = [test_result_document]
        with mock.patch.object(self.resource, "list_view") as mock_list_view:
            mock_cursor = mock.MagicMock()
            mock_cursor.__iter__ = mock.Mock(return_value=iter(test_list))
            mock_cursor.count = mock.Mock(return_value = len(test_list))
            mock_list_view.return_value = mock_cursor
            response = self.test_client.get("/cats")
            response_dict = json.loads(response.data.decode("utf-8"))
            self.assertEquals(response_dict["items"], test_result_list)
            self.assertEquals(response_dict["total_entries"], len(test_result_list))

    def test_pagination(self):
        test_document_id = ObjectId()
        test_document = {"_id":test_document_id, "breed":"tabby", "name":"muffins"}
        test_result_document = copy.deepcopy(test_document)
        test_result_document["id"] = str(test_result_document["_id"])
        del test_result_document["_id"]
        test_list = [copy.deepcopy(test_document) for x in range(0,40)]
        test_result_list = [copy.deepcopy(test_result_document) for x in range(0,40)]
        with mock.patch.object(self.resource, "list_view") as mock_list_view:
            mock_cursor = mock.MagicMock()
            mock_cursor.__iter__ = mock.Mock(return_value=iter(test_list))
            mock_cursor.count = mock.Mock(return_value = len(test_list))
            mock_cursor.sort = mock.Mock(return_value=mock_cursor)
            mock_cursor.limit = mock.Mock(return_value=mock_cursor)
            mock_cursor.skip = mock.Mock(return_value=mock_cursor)
            mock_list_view.return_value = mock_cursor
            response = self.test_client.get("/cats?page=2")
            response_dict = json.loads(response.data.decode("utf-8"))
            mock_cursor.limit.assert_called_once_with(25)
            mock_cursor.skip.assert_called_once_with(25)

    def test_item_get(self):
        test_document_id = ObjectId()
        test_document = {"_id":test_document_id, "breed":"tabby", "name":"muffins"}
        result_document = copy.deepcopy(test_document)
        result_document["id"] = str(test_document_id)
        del result_document["_id"]
        with mock.patch.object(self.resource, "item_view") as mock_item_view:
            mock_item_view.return_value = test_document
            response = self.test_client.get("/cats/{0}".format(test_document_id))
            response_dict = json.loads(response.data.decode("utf-8"))
            self.assertEquals(response_dict, result_document)

    def test_item_create(self):
        test_document_id = ObjectId()
        test_document = {"breed":"tabby", "name":"muffins"}
        def add_doc_id(document_to_create):
            document_to_create["id"] = test_document_id
        result_document = copy.deepcopy(test_document)
        result_document["id"] = str(test_document_id)
        with mock.patch.object(self.resource, "create_view", side_effect=add_doc_id) as mock_create_view:
            mongo_result = mock.MagicMock()
            mongo_result.inserted_id = test_document_id
            mock_create_view.return_value = mongo_result
            response = self.test_client.post("/cats", data=json.dumps(test_document))
            response_dict = json.loads(response.data.decode("utf-8"))
            self.assertEquals(response_dict, result_document)

    def test_item_update(self):
        test_document_id = "827f1f77bcd86cd712439045"
        existing_document = {"_id":ObjectId(test_document_id), "breed":"tabby", "name":"muffins"}
        update_document = {"_id":ObjectId(test_document_id), "breed":"tabby", "name":"scone"}
        self.mongo_collection.find_one.return_value = existing_document
        response = self.test_client.post("/cats/{0}".format(test_document_id), data=json.dumps({"name":"scone"}))
        self.mongo_collection.find_one_and_replace.assert_called_once_with({"_id":ObjectId(test_document_id)}, update_document)
        self.assertEquals(response.status_code, 204)

    def test_item_delete(self):
        test_document_id = "827f1f77bcd86cd712439045"
        response = self.test_client.delete("/cats/{0}".format(test_document_id))
        self.mongo_collection.find_one_and_delete.assert_called_once_with({"_id":ObjectId(test_document_id)})
        self.assertEquals(response.status_code, 204)



import json
import logging
import os.path
import sys
from unittest import TestCase, mock
import uuid

from flask import Flask
from flask.ext.ramlschema.resource import RAMLResource

logger = logging.getLogger(__name__)

class TestExampleApp(TestCase):
    def setUp(self):
        tests_dir = os.path.dirname(sys.modules[__name__].__file__)
        collection_raml_file = os.path.abspath(os.path.join(tests_dir, "../cats-collection.raml"))
        item_raml_file = os.path.abspath(os.path.join(tests_dir, "../cats-item.raml"))
        self.resource = RAMLResource.from_files(
            collection_raml_file, item_raml_file, "/cats", 
            logger, mock.MagicMock(), "test_database")
        self.flask_app = Flask("test_app")
        self.flask_app.config['TESTING'] = True
        self.test_client = self.flask_app.test_client()
        self.resource.init_app(self.flask_app)

    def tearDown(self):
        mock.patch.stopall()

    def test_list(self):
        test_document_id = str(uuid.uuid4().hex)
        test_document = {"_id":test_document_id, "breed":"tabby", "name":"muffins"}
        test_list = [test_document]
        with mock.patch.object(self.resource, "list_view") as mock_list_view:
            mock_cursor = mock.MagicMock()
            mock_cursor.__iter__ = mock.Mock(return_value=iter(test_list))
            mock_cursor.count = mock.Mock(return_value = len(test_list))
            mock_list_view.return_value = mock_cursor
            response = self.test_client.get("/cats")
            response_dict = json.loads(response.data.decode("utf-8"))
            self.assertEquals(response_dict["items"], test_list)
            self.assertEquals(response_dict["total_entries"], len(test_list))

    def test_item_get(self):
        test_document_id = str(uuid.uuid4().hex)
        test_document = {"_id":test_document_id, "breed":"tabby", "name":"muffins"}
        with mock.patch.object(self.resource, "item_view") as mock_item_view:
            mock_item_view.return_value = test_document
            response = self.test_client.get("/cats/{0}".format(test_document_id))
            response_dict = json.loads(response.data.decode("utf-8"))
            self.assertEquals(response_dict["item"], test_document)

    def test_item_create(self):
        test_document_id = str(uuid.uuid4().hex)
        test_document = {"breed":"tabby", "name":"muffins"}
        test_document_with_id = test_document.copy()
        test_document_with_id["_id"] = test_document_id
        with mock.patch.object(self.resource, "create_view") as mock_create_view:
            mongo_result = mock.MagicMock(wraps=test_document)
            mongo_result.inserted_id = test_document_id
            mock_create_view.return_value = mongo_result
            response = self.test_client.post("/cats", data=json.dumps({"item":test_document}))
            print(response.data)
            response_dict = json.loads(response.data.decode("utf-8"))
            test_document["id"] = test_document_id
            self.assertEquals(response_dict["item"], test_document)









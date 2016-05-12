import json
import logging
import os.path
import sys
from unittest import TestCase, mock

from flask import Flask
from flask.ext.ramlschema.resource import RAMLResource

logger = logging.getLogger(__name__)

class TestExampleApp(TestCase):
    def test_init_app(self):
    	tests_dir = os.path.dirname(sys.modules[__name__].__file__)
    	collection_raml_file = os.path.abspath(os.path.join(tests_dir, "../cats-collection.raml"))
    	item_raml_file = os.path.abspath(os.path.join(tests_dir, "../cats-item.raml"))
    	resource = RAMLResource.from_files(
    		collection_raml_file, item_raml_file, "/cats", 
    		logger, mock.MagicMock(), "test_database")
    	flask_app = Flask("test_app")
    	flask_app.config['TESTING'] = True
    	test_client = flask_app.test_client()
    	resource.init_app(flask_app)
    	test_document = {"breed":"tabby", "name":"muffins"}
    	test_list = [test_document]
    	with mock.patch.object(resource, "list_view") as mock_list_view:
    		mock_cursor = mock.MagicMock()
    		mock_cursor.__iter__ = mock.Mock(return_value=iter(test_list))
    		mock_cursor.count = mock.Mock(return_value = len(test_list))
    		mock_list_view.return_value = mock_cursor
	    	response = test_client.get("/cats/list")
	    	response_dict = json.loads(response.data.decode("utf-8"))
	    	self.assertEquals(response_dict["items"], test_list)


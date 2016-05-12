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
    	resource.init_app(flask_app)
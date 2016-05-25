.. code-block:: python

    from flask.ext.ramlschema import RAMLResource

    collection_raml_file = os.path.abspath(os.path.join(tests_dir, "../cats-collection.raml"))
    item_raml_file = os.path.abspath(os.path.join(tests_dir, "../cats-item.raml"))
    self.mongo_client = mock.MagicMock()
    self.resource = RAMLResource.from_files(
    	collection_raml_file, item_raml_file, "/cats", 
    	logger, self.mongo_client, "test_database"
    	)
    self.flask_app = Flask("test_app")
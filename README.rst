.. code-block:: python

    from flask.ext.ramlschema import RAMLResource

    collection_raml_file = "cats-collection.raml"
    item_raml_file = "cats-item.raml"
    resource = RAMLResource.from_files(
    	collection_raml_file, item_raml_file, "/cats", 
    	logger, self.mongo_client, "test_database"
    	)
    flask_app = Flask("test_app")
    resource.init_app(flask_app)
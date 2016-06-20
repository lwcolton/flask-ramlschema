.. image:: https://travis-ci.org/lwcolton/flask-ramlschema.svg?branch=master
    :target: https://travis-ci.org/lwcolton/flask-ramlschema

.. code-block:: python

    from flask.ext.ramlschema import RAMLResource

    collection_raml_file = "cats-collection.raml"
    item_raml_file = "cats-item.raml"
    flask_app = Flask("test_app")
    resource = RAMLResource.from_files(
    	flask_app, collection_raml_file, item_raml_file, "/cats", 
    	logger, mongo_client, "test_database"
    	)


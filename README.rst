.. image:: https://travis-ci.org/lwcolton/flask-ramlschema.svg?branch=master
    :target: https://travis-ci.org/lwcolton/flask-ramlschema

Create an API using RAML with JSONSchema

.. code-block:: python
    from flask import Flask
    from flask_ramlschema.views import RAMLResource
    from flask_ramlschema.errors import register_error_handlers
    from pymongo.mongo_client import MongoClient

    flask_app = Flask("test_app")
    register_error_handlers(flask_app)

    mongo_client = MongoClient("127.0.0.1", connect=False)

    collection_raml_file = "cats-collection.raml"
    item_raml_file = "cats-item.raml"

    resource = RAMLResource.from_files(
        collection_raml_file, item_raml_file, 
        url_path = "/cats", flask_app = flask_app,
        mongo_collection = mongo_client["flask-ramlschema-test"].cats
        )

See example_app.py and example-uwsgi.ini 
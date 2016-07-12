from flask import Flask
from flask_ramlschema.views import RAMLResource
from flask_ramlschema.errors import register_error_handlers
from pymongo.mongo_client import MongoClient

flask_app = Flask("test_app")
register_error_handlers(flask_app)

mongo_client = MongoClient("127.0.0.1", connect=False)

collection_raml_file = "raml/resources/cats-collection.raml"
item_raml_file = "raml/resources/cats-item.raml"

resource = RAMLResource.from_files(
    collection_raml_file, item_raml_file, 
    url_path = "/cats", flask_app = flask_app,
    mongo_collection = mongo_client["flask-ramlschema-test"].cats
    )



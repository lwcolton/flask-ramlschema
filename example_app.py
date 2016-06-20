import logging

from flask import Flask
from flask_ramlschema.resource import RAMLResource
from pymongo.mongo_client import MongoClient

collection_raml_file = "cats-collection.raml"
item_raml_file = "cats-item.raml"
flask_app = Flask("test_app")

logger = logging.getLogger(__name__)
mongo_client = MongoClient("127.0.0.1", connect=False)

resource = RAMLResource.from_files(
    flask_app, collection_raml_file, item_raml_file, "/cats",
    logger, mongo_client, "test_database"
    )

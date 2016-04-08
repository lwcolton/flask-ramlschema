import os.path

from default_logger import get_default_logger
import yaml

from .resource import RAMLResource

class RAMLSchemaExtension:
    def __init__(self, mongo_client, database_name, raml_directory=None, logger=None):
        self.mongo_client = mongo_client
        self.database_name = database_name
        self.raml_directory = raml_directory
        if logger is None:
            logger = get_default_logger("ramlschema")
        self.logger = logger
        self.resources = {}

    def add_resource(self, flask_app, path, raml_path, resource_class=None, **kwargs):
        if path in self.resources:
            raise ValueError("Will overwrite existing resource: {0}".format(path))
        mongo_client = kwargs.pop("mongo_client", self.mongo_client)
        database_name = kwargs.pop("database_name", self.database_name)
        if self.raml_directory:
            raml_path = os.path.join(self.raml_directory, raml_path)
        with open(raml_path, "r") as raml_handle:
            raml = yaml.load(raml_handle.read())
        if resource_class is None:
            resource_class = RAMLResource
        resource = resource_class(path, raml, mongo_client, database_name, **kwargs)
        resource.init_app(flask_app)
        self.resources[path] = resource
        return resource
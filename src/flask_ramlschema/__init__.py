import os.path

from default_logger import get_default_logger
from flask import request
import json
import jsonschema
import yaml

class RAMLResource:
    def __init__(self, path, raml, logger, mongo_collection):
        self.path = path
        self.raml = raml
        self.logger = logger
        self.mongo_collection = mongo_collection
        self.parse_raml()

    def parse_raml(self):
        if "collection" not in self.raml["type"]:
            raise NotImplementedError("Only support collections")
        json_schema_string = self.raml["schema"]
        self.new_item_schema = json.loads(self.raml["type"]["collection"]["newItemSchema"])

        child_paths = [key for key in list(self.raml.keys()) if key.startswith("/")]
        if len(child_paths) > 1:
            raise NotImplementedError("Only supports one child path")
        elif len(child_paths) == 0:
            raise NotImplementedError("Collection must also implement ID based collection-item")

        child_path = child_paths[0]
        if not child_path.startswith("/{") or not child_path.endswith("}"):
            raise NotImplementedError("Only supports one sub-path for ID parameter")
        self.id_param_name = child_path[1:-1]
        self.id_path = self.path + child_path
        self.update_item_schema = json.loads(self.raml[child_path]["type"]["collection"]["updateItemSchema"])
        self.logger.info("Loaded {0}".format(self.path))

    def init_app(self, app):
        app.

    def validate_request(self):
        jsonschema.validate(request_data, self.json_schema)

    def list_view(self):
        page = request.args.get("page", 1)
        per_page = request.args.get("per_page", 25)
        if per_page > 100:
            raise ValueError("per_page cannot be greated than 100")

        sort_by = request.args.get("sort_by", "id")
        if sort_by == "id":
            sort_by = "_id"

        # order values based on backbone-paginator
        order = request.args.get("order", 1)
        if order == 1:
            order = pymongo.DESCENDING
        else:
            order = pymongo.ASCENDING
        
        find_cursor = self.mongo_collection.find()
        total_entries = find_cursor.count()
        page_wrapper = {}
        page_wrapper["page"] = page
        page_wrapper["per_page"] = per_page
        page_wrapper["total_pages"] = int(math.ceil(total_entries / float(page_wrapper["per_page"])))
        page_wrapper["total_entries"] = total_entries
        page_wrapper["sort_by"] = sort_by
        page_wrapper["order"] = int(params.get("order", 1))

        if page_wrapper["page"] > page_wrapper["total_pages"] or page_wrapper["page"] < 1:
            if queryset_length != 0 or page_wrapper["page"] != 1:
                raise ValueError("invalid page number: {0]".format(page_wrapper["page"]))

        end = page_wrapper["page"] * page_wrapper["per_page"]
        start = end - page_wrapper["per_page"]
        if end > queryset_length:
            end = queryset_length

        items = list(find_cursor.sort(sort_by, order).skip(per_page*(page-1)).limit(per_page))
        page_wrapper["items"] = items
        response.json = page_wrapper



class RAMLSchemaExtension:
    def __init__(self, resources_dir, logger=None):
        if logger is None:
            logger = get_default_logger("ramlschema")
        self.logger = logger
        self.resources_dir = resources_dir
        self.resources = self.load_resources_from_dir(resources_dir)

    def load_resources_from_dir(self, resources_dir):
        self.logger.info("Loading RAML resources from {0}".format(resources_dir))
        resources = []
        for file_name in os.listdir(resources_dir):
            key = file_name.split('.')[0]
            file_path = os.path.join(resources_dir, file_name)
            if os.path.isdir(file_path):
                self.logger.info("Skipping directory: {0}".format(file_name))
                continue
            elif not file_path.endswith(".raml"):
                self.logger.info("Skipping file without .raml extension: {0}".format(file_name))
                continue
            with open(file_path) as file_handle:
                self.logger.info("Loading {0}".format(file_name))
                raml = yaml.loads(file_handle.read())
                path = "/" + key
                resources.append(RAMLResource(path, raml, self.logger))
        return resources

    def init_app(self, app):
        for resource in self.resources:

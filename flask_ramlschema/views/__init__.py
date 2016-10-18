import flask

from .errors import BodyValidationHTTPError
from ..json_encoder import JSONEncoder
from ..validate import body_validators

class ResourceView(flask.MethodView):
    def __init__(self, endpoints_raml):
        self.endpoints_raml = endpoints_raml
        self.methods = []
        for allowed_method in self.endpoints_raml.keys():
            self.methods.append(allowed_method)

    def json_response(self, response_dict, status=200):
        response = flask.Response()
        response.data = JSONEncoder().encode(response_dict)
        response.mimetype = "application/json"
        response.status_code = 200
        return response

    @property
    def method_raml(self):
        return self.endpoints_raml.get(request.method)

    def dispatch_request(self, *args, **kwargs):
        self.validate_request()
        response_data = super().dispatch_request(*args, **kwargs)
        if response_data is not None:
            if content_type == "application/json":
                return self.json_response(response_data)

    def validate_request(self):
        content_type = flask.request.headers.get("content-type")
        if content_type == "application/json":
            self.validate_request_json()

    def validate_request_json(self):
        body_schema = getattr(self.method_raml.body, "schema", None)
        if body_schema:
            try:
                errors = get_json_errors(request.json, endpoint_raml.schema)
                if errors:
                    raise BodyValidationHTTPError(errors)
            except json.JSONDecodeError as decode_error:
                raise self.body_decode_error_class(decode_error)

class ModelView(ResourceView):
    model = None

    @classmethod
    def add_url_rule(cls, app, resource_path, *args, **kwargs):
        model = None
        if cls.model is None and "model" not in kwargs:
            model_name = resource_path.split("/")[0]
            model = ModelType(model_name, Model, {"collection_name":model_name.lower()})
        view = cls(*args, **kwargs)
        app.add_url_rule(resource_path, view.dispatch_request)


    def __init__(self, *args, **kwargs):
        model = kwargs.pop("model")
        if model is not None:
            self.model = model
        super().__init__(*args, **kwargs)

    def find_one_or_404(self, document_id, model=None):
        if model is None:
            model = self.model
        document = model.find_one_id(document_id)
        if not document:
            abort(404)
        return document

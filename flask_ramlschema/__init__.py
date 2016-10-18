import ramlfications

from .views import CollectionView, CollectionItemView
from .collection_model import CollectionModel
from . import setting_names

def init_app(app, raml_source):
    resources = {}
    raml_api = ramlfications.parse(raml_source)
    for endpoint in raml_api.resources:
        resources.setdefault(endpoint.path, {})
        resources[endpoint.path][endpoint.method.upper()] = endpoint
        if endpoint.path not in path_views:
            resource_type = getattr(resource, "type", None)
            path_views[endpoint.path] = resource_type_views[resource_type]

    for resource_path, endpoints in resources.items():
        view_class = path_views[resource_path]
        if hasattr(view_class, "add_url_rule"):
            view_class.add_url_rule(app, resource_path, endpoints)
        else:
            view = view_class(endpoints)
            app.add_url_rule(resource_path, view.dispatch_request)

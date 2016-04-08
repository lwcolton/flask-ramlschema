from .resource import RAMLResource

class StormpathResource(RAMLResource):
    def __init__(self, *args, groups_required, all_groups=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.groups_required = groups_required
        self.all_groups = all_groups

    


    def init_app(self, flask_app, *args, **kwargs):
        super().init_app(*args, **kwargs)
        if app.before_request_funcs is None:
            app.before_request_funcs = {}
        app.before_request_funcs.setdefault(None, [])
        app.before_request_funcs[None].append(self.validate_current_request)

    def validate_current_request(self):
        url_rule
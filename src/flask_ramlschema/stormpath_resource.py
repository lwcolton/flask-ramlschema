from flask.ext.stormpath.authorization import user_has_groups

from .resource import RAMLResource

class StormpathResource(RAMLResource):
    def __init__(self, *args, create_groups, view_groups, update_groups, delete_groups, admin_groups, **kwargs):
        super().__init__(*args, **kwargs)
        self.create_groups = create_groups
        self.view_groups = view_groups
        self.update_groups = update_groups
        self.delete_groups = delete_groups
        self.admin_groups = admin_groups

    def create_allowed(self, *args, **kwargs):
        return (
            user_has_groups(self.create_groups) or \
            user_has_groups(self.admin_groups)
        )

    def list_allowed(self, *args, **kwargs):
        return self.view_allowed()


    def update_allowed(self, *args, **kwargs):
        return (
            user_has_groups(self.update_groups) or \
            user_has_groups(self.admin_groups)
        )

    def item_view_allowed(self, *args, **kwargs):
        return (
            user_has_groups(self.view_groups) or \
            user_has_groups(self.admin_groups)
        )

    def delete_allowed(self, *args, **kwargs):
        return (
            user_has_groups(self.delete_groups) or \
            user_has_groups(self.admin_groups)
        )

    # Not part of RAMLResource API
    def view_allowed(self, *args, **kwargs):
        return (
            user_has_groups(self.view_groups) or \
            user_has_groups(self.admin_groups)
        )

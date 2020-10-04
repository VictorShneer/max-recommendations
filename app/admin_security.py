from flask_admin.contrib.sqla import ModelView
from flask_admin import AdminIndexView
from flask_login import current_user
from flask import current_app
from flask import redirect, url_for

class MyModelView(ModelView):
    def __init__(self, model, session, name=None, category=None, endpoint=None, url=None, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
        super(MyModelView, self).__init__(model, session, name=name, category=category, endpoint=endpoint, url=url)

    def is_accessible(self):
        current_roles = [role.name for role in current_user.roles]
        return (current_user.is_authenticated and current_app.config['ADMIN_ROLE_TITLE'] in current_roles)

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('auth.login'))

class MyAdminIndexView(AdminIndexView):
    def is_accessible(self):
        current_roles = [role.name for role in current_user.roles]
        return (current_user.is_authenticated and current_app.config['ADMIN_ROLE_TITLE'] in current_roles)

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('auth.login'))

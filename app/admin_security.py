from flask_admin.contrib.sqla import ModelView
from flask_admin import AdminIndexView
from flask_login import current_user
from flask import redirect, url_for

class MyModefView(ModelView):
    def is_accessible(self):
        return (current_user.is_authenticated)

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('auth.login'))

class MyAdminIndexView(AdminIndexView):
    def is_accessible(self):
        # current_roles = [role.name for role in current_user.roles]

        # 'admin' in current_roles
        return (current_user.is_authenticated)

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('auth.login'))

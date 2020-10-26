"""
Admin security rules
We check if current user is authenticated and has proper role to view admin pages
TODO duplicated code need refactor
"""
from flask_admin.contrib.sqla import ModelView
from flask_admin import AdminIndexView, expose
from flask_login import current_user
from flask import current_app
from flask import redirect, url_for
from app.admin.forms import AssignCryptoForm
from app import db

class MyModelView(ModelView):
    def __init__(self, model, session, name=None, category=None, endpoint=None, url=None, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
        super(MyModelView, self).__init__(model, session, name=name, category=category, endpoint=endpoint, url=url)

    def is_accessible(self):
        if not current_user.is_authenticated:
            return False
        current_roles = [role.name for role in current_user.roles]
        return current_app.config['ADMIN_ROLE_TITLE'] in current_roles


    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('auth.login'))

class MyAdminIndexView(AdminIndexView):
    @expose('/', methods=['GET', 'POST'])
    def index(self):
        form = AssignCryptoForm()
        if form.validate_on_submit():
            user_id = form.user_id.data
            crypto = form.crypto.data
            current_user.launch_task('assign_crypto_to_user_id',\
                                    'Присваиваю крипто и создаю базы в кликхаусе.', \
                                    current_user.id, user_id,crypto)
            db.session.commit()
        return self.render('admin/adminindex.html', form=form)

    def is_accessible(self):
        if not current_user.is_authenticated:
            return False
        current_roles = [role.name for role in current_user.roles]
        return current_app.config['ADMIN_ROLE_TITLE'] in current_roles

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('auth.login'))

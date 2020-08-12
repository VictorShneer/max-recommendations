from app.models import User, Integration
from flask_login import current_user
from flask import abort

def current_user_own_integration(function):
    def wrapper(integration_id):
        integration = Integration.query.filter_by(id=integration_id).first_or_404()
        print(integration)
        if current_user.id != integration.user_id:
            print('Permission abort')
            abort(404)
        else:
            function(integration_id)
            return print("SUCCESS")
    return wrapper

from app.models import User, Integration
# legacy
def current_user_own_integration(integration, current_user):
    return False if any([current_user.crypto is None, current_user != integration.user]) else True

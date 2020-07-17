from app.models import User, Integration

def current_user_own_integration(integration, current_user):
    return False if current_user != integration.user else True

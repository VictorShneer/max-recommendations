from app.models import User, Integration
from flask_login import current_user
from flask import abort
import requests
from flask import current_app

def current_user_own_integration(function):
    def wrapper(integration_id):
        integration = Integration.query.filter_by(id=integration_id).first_or_404()
        if current_user.id != integration.user_id:
            print('Permission abort')
            abort(404)
        else:
            return function(integration_id)
    # Renaming the function name:
    wrapper.__name__ = function.__name__
    return wrapper

def create_url_for_query(query,db_name):
    host = current_app.config['CLICKHOUSE_HOST']
    return 'https://{host}:8443/?database={db}&query={query}'.format(host=host, db=db_name, query=query)

def send_request_to_clickhouse(url):
    certificate_path = 'app/YandexInternalRootCA.crt'
    auth = {'X-ClickHouse-User': current_app.config['CLICKHOUSE_LOGIN'],'X-ClickHouse-Key': current_app.config['CLICKHOUSE_PASSWORD']}
    r = requests.get(url = url, headers=auth, verify=certificate_path)
    return r
